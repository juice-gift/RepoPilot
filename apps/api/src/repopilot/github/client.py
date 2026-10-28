"""Read-only official GitHub MCP boundary; no model-selected endpoint or writes."""

import base64
import hashlib
import json
import logging
import re
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

import anyio
import httpx2
from jsonschema import Draft202012Validator
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from repopilot.config import Settings
from repopilot.resolution.workspace import safe_path

ENDPOINT = "https://api.githubcopilot.com/mcp/"
READ_TOOLS = frozenset(
    {
        "get_me",
        "get_commit",
        "get_file_contents",
        "issue_read",
        "pull_request_read",
        "list_pull_requests",
    }
)
MAX_RESPONSE_BYTES = 1_048_576
MAX_RESULT_BYTES = 128_000
OPERATION_SECONDS = 30
_private_logs: ContextVar[bool] = ContextVar("github_mcp_private_logs", default=False)


class GitHubMCPError(RuntimeError):
    """Only application-owned codes cross this boundary, never SDK exception text."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class _PrivateLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _private_logs.get()


@contextmanager
def private_transport_logs() -> Iterator[None]:
    # SDK debug/SSE/exception logs can contain full untrusted payloads. Suppress
    # only this async context, preserving other requests and application logging.
    token = _private_logs.set(True)
    log_filter = _PrivateLogFilter()
    names = ["mcp", "httpx2", "httpcore2"] + list(logging.Logger.manager.loggerDict)
    loggers = [
        logging.getLogger(n)
        for n in set(names)
        if n.split(".")[0] in {"mcp", "httpx2", "httpcore2"}
    ]
    for logger in loggers:
        logger.addFilter(log_filter)
    try:
        yield
    finally:
        for logger in loggers:
            logger.removeFilter(log_filter)
        _private_logs.reset(token)


class _BoundedStream(httpx2.AsyncByteStream):
    def __init__(self, stream: httpx2.AsyncByteStream) -> None:
        self.stream = stream

    async def __aiter__(self) -> AsyncIterator[bytes]:
        size = 0
        async for chunk in self.stream:
            size += len(chunk)
            if size > MAX_RESPONSE_BYTES:
                raise GitHubMCPError("response_limit")
            yield chunk

    async def aclose(self) -> None:
        await self.stream.aclose()


class OfficialTransport(httpx2.AsyncBaseTransport):
    """Credential-bearing requests can reach only the fixed official endpoint."""

    def __init__(self) -> None:
        self._transport = httpx2.AsyncHTTPTransport(retries=0)

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        if str(request.url) != ENDPOINT or request.method not in {
            "GET",
            "POST",
            "DELETE",
        }:
            raise GitHubMCPError("endpoint_denied")
        response = await self._transport.handle_async_request(request)
        # Request identity encoding so the byte bound also bounds JSON decoding.
        if response.headers.get("content-encoding", "identity").lower() != "identity":
            await response.aclose()
            raise GitHubMCPError("encoding_denied")
        response.stream = _BoundedStream(response.stream)
        return response

    async def aclose(self) -> None:
        await self._transport.aclose()


def _safe_error(exc: Exception) -> GitHubMCPError:
    pending = [exc]
    for _ in range(32):
        if not pending:
            break
        current = pending.pop()
        if isinstance(current, GitHubMCPError):
            return current
        if isinstance(current, httpx2.HTTPStatusError):
            if current.response.status_code == 401:
                return GitHubMCPError("authentication_failed")
            if current.response.status_code == 403:
                return GitHubMCPError("permission_denied")
        if isinstance(current, (TimeoutError, httpx2.TimeoutException)):
            return GitHubMCPError("timeout")
        if isinstance(current, ExceptionGroup):
            pending.extend(current.exceptions)
    return GitHubMCPError("transport_failure")


@dataclass(frozen=True)
class ToolData:
    # Untrusted data for subsequent typed adapters. Links are never dereferenced.
    name: str
    data: dict[str, object]


class GitHubReadClient:
    def __init__(self, client: Client, settings: Settings) -> None:
        self._client = client
        self._repositories = frozenset(settings.github_mcp_allowed_repositories)
        self._token = settings.github_mcp_token
        self._schemas: dict[str, dict[str, object]] = {}
        self.calls = 0

    @property
    def connection_evidence(self) -> dict[str, object]:
        # Server identity is untrusted. Retain only bounded, token-redacted fields.
        info = self._client.server_info
        token = self._token.get_secret_value() if self._token else ""

        def safe(value: str) -> str:
            return value.replace(token, "[REDACTED]")[:120] if token else value[:120]

        return {
            "endpoint": ENDPOINT,
            "protocol": safe(self._client.protocol_version),
            "server_name": safe(info.name) if info else None,
            "server_version": safe(info.version) if info else None,
            "tools": {
                name: hashlib.sha256(
                    json.dumps(schema, sort_keys=True).encode()
                ).hexdigest()
                for name, schema in sorted(self._schemas.items())
            },
            "readonly": True,
        }

    async def discover(self) -> None:
        schemas: dict[str, dict[str, object]] = {}
        seen_names: set[str] = set()
        cursors: set[str] = set()
        cursor = None
        with anyio.fail_after(OPERATION_SECONDS):
            for _ in range(8):
                page = await self._client.list_tools(
                    cursor=cursor, cache_mode="refresh"
                )
                if len(page.tools) > 100 or len(seen_names) + len(page.tools) > 100:
                    raise GitHubMCPError("discovery_limit")
                for tool in page.tools:
                    if tool.name in seen_names or tool.name not in READ_TOOLS:
                        raise GitHubMCPError("discovery_denied")
                    seen_names.add(tool.name)
                    schema = tool.input_schema
                    # No remote schema references: validation must not fetch URLs.
                    encoded = json.dumps(schema)
                    if len(encoded) > 24_000 or '"$ref"' in encoded:
                        raise GitHubMCPError("schema_denied")
                    Draft202012Validator.check_schema(schema)
                    if schema.get("type") != "object":
                        raise GitHubMCPError("schema_denied")
                    schemas[tool.name] = schema
                if page.next_cursor is None:
                    if "get_me" not in schemas:
                        raise GitHubMCPError("discovery_incomplete")
                    self._schemas = schemas
                    return
                if page.next_cursor in cursors:
                    raise GitHubMCPError("discovery_cycle")
                cursors.add(page.next_cursor)
                cursor = page.next_cursor
        raise GitHubMCPError("discovery_limit")

    def _repository(self, repository: str) -> dict[str, object]:
        if repository.lower() not in self._repositories:
            raise GitHubMCPError("repository_denied")
        owner, repo = repository.lower().split("/")
        return {"owner": owner, "repo": repo}

    async def _call(self, name: str, arguments: dict[str, object]) -> ToolData:
        if name not in READ_TOOLS or name not in self._schemas:
            raise GitHubMCPError("operation_denied")
        if name != "get_me":
            repository = f"{arguments.get('owner', '')}/{arguments.get('repo', '')}"
            self._repository(repository)
        if (
            name in {"issue_read", "pull_request_read"}
            and arguments.get("method") != "get"
        ):
            raise GitHubMCPError("operation_denied")
        if not Draft202012Validator(self._schemas[name]).is_valid(arguments):
            raise GitHubMCPError("arguments_invalid")
        if self.calls >= 24:
            raise GitHubMCPError("call_limit")
        self.calls += 1
        try:
            with anyio.fail_after(OPERATION_SECONDS):
                result = await self._client.call_tool(name, arguments)
            if result.is_error:
                raise GitHubMCPError("tool_failed")
            encoded = result.model_dump_json()
            if len(encoded.encode()) > MAX_RESULT_BYTES:
                raise GitHubMCPError("result_limit")
            if self._token:
                token = self._token.get_secret_value()
                for secret in (token, base64.b64encode(token.encode()).decode()):
                    encoded = encoded.replace(secret, "[REDACTED]")
            return ToolData(name, json.loads(encoded))
        except Exception as exc:  # noqa: BLE001 - sanitize third-party failures at the trust boundary
            raise _safe_error(exc) from None

    async def identity(self) -> ToolData:
        return await self._call("get_me", {})

    async def commit(self, repository: str, ref: str) -> ToolData:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}", ref) or ".." in ref:
            raise GitHubMCPError("ref_denied")
        return await self._call(
            "get_commit", {**self._repository(repository), "sha": ref, "detail": "none"}
        )

    async def file(self, repository: str, path: str, commit: str) -> ToolData:
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise GitHubMCPError("commit_required")
        if path:
            try:
                safe_path(path)
            except ValueError:
                raise GitHubMCPError("path_denied") from None
        return await self._call(
            "get_file_contents",
            {
                **self._repository(repository),
                "path": path,
                "ref": commit,
            },
        )

    async def issue(self, repository: str, number: int) -> ToolData:
        if type(number) is not int or not 1 <= number <= 2_147_483_647:
            raise GitHubMCPError("number_denied")
        return await self._call(
            "issue_read",
            {
                **self._repository(repository),
                "method": "get",
                "issue_number": number,
            },
        )

    async def pull_request(self, repository: str, number: int) -> ToolData:
        if type(number) is not int or not 1 <= number <= 2_147_483_647:
            raise GitHubMCPError("number_denied")
        return await self._call(
            "pull_request_read",
            {
                **self._repository(repository),
                "method": "get",
                "pullNumber": number,
            },
        )

    async def pull_requests(self, repository: str) -> ToolData:
        return await self._call(
            "list_pull_requests",
            {
                **self._repository(repository),
                "state": "all",
                "perPage": 10,
                "page": 1,
            },
        )


@asynccontextmanager
async def connect_github_readonly(
    settings: Settings,
) -> AsyncIterator[GitHubReadClient]:
    secret = settings.github_mcp_token
    if secret is None or not secret.get_secret_value().strip():
        raise GitHubMCPError("credential_missing")
    token = secret.get_secret_value()
    if any(ord(char) < 33 or ord(char) > 126 for char in token):
        raise GitHubMCPError("credential_invalid")
    with private_transport_logs():
        try:
            async with httpx2.AsyncClient(
                headers={
                    "Authorization": "Bearer " + token,
                    "X-MCP-Readonly": "true",
                    "X-MCP-Tools": ",".join(sorted(READ_TOOLS)),
                    "Accept-Encoding": "identity",
                },
                transport=OfficialTransport(),
                timeout=httpx2.Timeout(15, read=30),
                follow_redirects=False,
                trust_env=False,
            ) as http:
                transport = streamable_http_client(
                    ENDPOINT, http_client=http, max_sse_event_size=MAX_RESPONSE_BYTES
                )
                async with Client(
                    transport,
                    read_timeout_seconds=30,
                    cache=None,
                    input_required_max_rounds=0,
                ) as client:
                    reader = GitHubReadClient(client, settings)
                    await reader.discover()
                    yield reader
        except Exception as exc:  # noqa: BLE001 - never expose SDK/network exception payloads
            raise _safe_error(exc) from None
