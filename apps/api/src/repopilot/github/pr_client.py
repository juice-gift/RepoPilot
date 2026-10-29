"""An approval-scoped official MCP session exposing only exact draft-PR creation."""

import hashlib
import json
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
import httpx2
from jsonschema import Draft202012Validator
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from repopilot.config import Settings
from repopilot.github.client import (
    ENDPOINT,
    MAX_RESPONSE_BYTES,
    MAX_RESULT_BYTES,
    GitHubMCPError,
    OfficialTransport,
    ToolData,
    private_transport_logs,
)
from repopilot.github.git_api import require_write_scope
from repopilot.github.probe import object_payload
from repopilot.github.proposals import PublicationPlan

PR_TOOLS = frozenset({"create_pull_request", "list_pull_requests", "pull_request_read"})


class ApprovedPRClient:
    def __init__(self, client: Client, plan: PublicationPlan) -> None:
        self.client, self.plan = client, plan
        self.schemas: dict[str, dict] = {}
        self.calls = 0

    @property
    def connection_evidence(self) -> dict:
        version = self.client.protocol_version
        return {
            "endpoint": ENDPOINT,
            "protocol": version
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", version)
            else "unrecognized",
            "tools": {
                name: hashlib.sha256(
                    json.dumps(schema, sort_keys=True).encode()
                ).hexdigest()
                for name, schema in sorted(self.schemas.items())
            },
            "write_operation": "create_pull_request",
        }

    async def discover(self) -> None:
        with anyio.fail_after(30):
            page = await self.client.list_tools(cache_mode="refresh")
        if (
            page.next_cursor is not None
            or len(page.tools) != len(PR_TOOLS)
            or {t.name for t in page.tools} != PR_TOOLS
        ):
            raise GitHubMCPError("publication_discovery_denied")
        for tool in page.tools:
            schema = tool.input_schema
            encoded = json.dumps(schema)
            if (
                len(encoded) > 24000
                or any(
                    key in encoded
                    for key in ('"$ref"', '"$dynamicRef"', '"$recursiveRef"')
                )
                or schema.get("type") != "object"
            ):
                raise GitHubMCPError("schema_denied")
            Draft202012Validator.check_schema(schema)
            self.schemas[tool.name] = schema
        if not Draft202012Validator(self.schemas["create_pull_request"]).is_valid(
            self.create_arguments
        ) or not Draft202012Validator(self.schemas["list_pull_requests"]).is_valid(
            self.find_arguments
        ):
            raise GitHubMCPError("publication_arguments_denied")

    async def _call(self, name: str, args: dict) -> ToolData:
        allowed = (
            (name == "create_pull_request" and args == self.create_arguments)
            or (name == "list_pull_requests" and args == self.find_arguments)
            or (
                name == "pull_request_read"
                and args.get("method") == "get"
                and type(args.get("pullNumber")) is int
                and args["pullNumber"] > 0
                and args
                == {**self.scope, "method": "get", "pullNumber": args["pullNumber"]}
            )
        )
        if (
            not allowed
            or name not in self.schemas
            or not Draft202012Validator(self.schemas[name]).is_valid(args)
        ):
            raise GitHubMCPError("publication_arguments_denied")
        self.calls += 1
        if self.calls > 8:
            raise GitHubMCPError("call_limit")
        with anyio.fail_after(30):
            result = await self.client.call_tool(name, args)
        if result.is_error:
            raise GitHubMCPError(
                "pr_tool_failed_ambiguous"
                if name == "create_pull_request"
                else "pr_read_failed"
            )
        if len(result.model_dump_json().encode()) > MAX_RESULT_BYTES:
            raise GitHubMCPError("result_limit")
        return ToolData(name, json.loads(result.model_dump_json()))

    @property
    def scope(self) -> dict[str, str]:
        owner, repo = self.plan.repository.split("/")
        return {"owner": owner, "repo": repo}

    async def find(self) -> list[dict]:
        data = await self._call("list_pull_requests", self.find_arguments)
        result = data.data.get("structured_content")
        if (
            not isinstance(result, list)
            or len(result) > 1
            or any(not isinstance(p, dict) for p in result)
        ):
            raise GitHubMCPError("pr_collision")
        return result

    async def get(self, number: int) -> dict:
        if type(number) is not int or number < 1:
            raise GitHubMCPError("pr_identity_invalid")
        data = await self._call(
            "pull_request_read", {**self.scope, "method": "get", "pullNumber": number}
        )
        payload = object_payload(data)
        result = payload.get("pull_request", payload)
        if not isinstance(result, dict):
            raise GitHubMCPError("pr_response_invalid")
        return result

    async def create(self) -> None:
        # Arguments are rebuilt from the approved plan; never provided by an LLM.
        await self._call("create_pull_request", self.create_arguments)

    @property
    def create_arguments(self) -> dict:
        p = self.plan
        return {
            **self.scope,
            "head": p.head_branch,
            "base": "main",
            "title": p.pr_title,
            "body": p.pr_body,
            "draft": True,
            "maintainer_can_modify": False,
        }

    @property
    def find_arguments(self) -> dict:
        return {
            **self.scope,
            "head": f"{self.scope['owner']}:{self.plan.head_branch}",
            "base": "main",
            "state": "all",
            "perPage": 2,
            "page": 1,
        }


@asynccontextmanager
async def _pr_session(
    settings: Settings, plan: PublicationPlan
) -> AsyncIterator[ApprovedPRClient]:
    if plan.repository not in settings.github_mcp_allowed_repositories:
        raise GitHubMCPError("repository_denied")
    if settings.github_mcp_token is None:
        raise GitHubMCPError("credential_missing")
    token = settings.github_mcp_token.get_secret_value()
    if not token or any(ord(c) < 33 or ord(c) > 126 for c in token):
        raise GitHubMCPError("credential_invalid")
    with private_transport_logs():
        try:
            async with httpx2.AsyncClient(
                headers={
                    "Authorization": "Bearer " + token,
                    "X-MCP-Tools": ",".join(sorted(PR_TOOLS)),
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
                    scoped = ApprovedPRClient(client, plan)
                    await scoped.discover()
                    yield scoped
        except GitHubMCPError:
            raise
        except Exception:  # noqa: BLE001 - sanitize all SDK errors, including ambiguous writes
            raise GitHubMCPError("pr_transport_ambiguous") from None


@asynccontextmanager
async def connect_approved_pr(
    settings: Settings, plan: PublicationPlan, approved_hash: str
) -> AsyncIterator[ApprovedPRClient]:
    require_write_scope(settings, plan, approved_hash)
    async with _pr_session(settings, plan) as client:
        yield client


async def inspect_pr_support(settings: Settings, plan: PublicationPlan) -> dict:
    """Discovery and a filtered PR read only; never call a mutation before approval."""
    async with _pr_session(settings, plan) as client:
        existing = await client.find()
        return {
            "connection": client.connection_evidence,
            "matching_pr_count": len(existing),
            "remote_writes": 0,
        }
