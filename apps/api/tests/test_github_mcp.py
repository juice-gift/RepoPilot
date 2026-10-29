"""Local protocol/policy tests, explicitly not actual GitHub acceptance evidence."""

import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import anyio
import httpx2
import pytest
from mcp import Client
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent
from pydantic import SecretStr

from repopilot.config import Settings
from repopilot.github.client import (
    ENDPOINT,
    GitHubMCPError,
    GitHubReadClient,
    OfficialTransport,
    _BoundedStream,
    _safe_error,
    connect_github_readonly,
    private_transport_logs,
)
from repopilot.github.probe import object_payload, probe
from repopilot.resolution.sandbox import docker_environment


def settings(**kwargs):
    return Settings(
        _env_file=None, database_url="postgresql+psycopg://test/db", **kwargs
    )


def tool(name="get_me", schema=None):
    return SimpleNamespace(name=name, input_schema=schema or {"type": "object"})


def fake_client(tools=None):
    return SimpleNamespace(
        list_tools=AsyncMock(
            return_value=SimpleNamespace(
                tools=tools or [tool()],
                next_cursor=None,
            )
        ),
        call_tool=AsyncMock(
            return_value=CallToolResult(
                content=[TextContent(type="text", text='{"login":"test"}')],
            )
        ),
        server_info=None,
        protocol_version="2026-07-28",
    )


def test_token_loads_from_dotenv_is_excluded_and_env_takes_precedence(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("GITHUB_MCP_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("GITHUB_MCP_TOKEN=local-test-credential\n", encoding="utf-8")
    configured = Settings(
        _env_file=env_file, database_url="postgresql+psycopg://test/db"
    )
    assert configured.github_mcp_token.get_secret_value() == "local-test-credential"
    assert "local-test-credential" not in repr(configured)
    assert "github_mcp_token" not in configured.model_dump()
    assert "local-test-credential" not in configured.model_dump_json()
    monkeypatch.setenv("GITHUB_MCP_TOKEN", "environment-test-credential")
    assert (
        Settings(
            _env_file=env_file, database_url="postgresql+psycopg://test/db"
        ).github_mcp_token.get_secret_value()
        == "environment-test-credential"
    )


def test_github_credential_never_enters_sandbox_environment(monkeypatch):
    for name in ("GITHUB_MCP_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN", "GH_TOKEN"):
        monkeypatch.setenv(name, "test-credential")
        assert name not in docker_environment()


@pytest.mark.parametrize(
    "credential,code",
    [
        (None, "credential_missing"),
        ("", "credential_missing"),
        ("x\ny", "credential_invalid"),
    ],
)
def test_bad_credential_fails_before_transport(credential, code):
    async def run():
        with pytest.raises(GitHubMCPError, match=code):
            async with connect_github_readonly(settings(github_mcp_token=credential)):
                pytest.fail("Must not connect")

    anyio.run(run)


def test_allowlist_canonicalization_and_no_wildcards():
    assert settings(
        github_mcp_allowed_repositories=["Juice-Gift/Test", "juice-gift/test"]
    ).github_mcp_allowed_repositories == ["juice-gift/test"]
    for value in (
        "*",
        "juice-gift/*",
        "https://github.com/juice-gift/test",
        "juice-gift/..",
    ):
        with pytest.raises(ValueError):
            settings(github_mcp_allowed_repositories=[value])


def test_actual_sdk_protocol_in_memory_and_safe_result_parsing():
    server = MCPServer("local-protocol-test")

    @server.tool()
    def get_me() -> dict[str, str]:
        return {"login": "test"}

    async def run():
        async with Client(server, input_required_max_rounds=0, cache=None) as client:
            reader = GitHubReadClient(client, settings())
            await reader.discover()
            assert object_payload(await reader.identity()) == {"login": "test"}
            assert reader.connection_evidence["protocol"] == "2026-07-28"
            assert reader.calls == 1

    anyio.run(run)


def test_complete_readonly_http_lifecycle_headers_and_probe(monkeypatch, caplog):
    """Actual SDK HTTP protocol against local ASGI, not GitHub integration."""
    server = MCPServer("local-http-protocol-test")

    @server.tool()
    def get_me() -> dict[str, str]:
        return {"login": "test"}

    app = server.streamable_http_app(
        streamable_http_path="/mcp/",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["api.githubcopilot.com"],
        ),
    )

    async def run():
        observed = []
        asgi = httpx2.ASGITransport(app)

        async def respond(request):
            assert str(request.url) == ENDPOINT
            assert request.headers["authorization"] == "Bearer test-secret"
            assert request.headers["x-mcp-readonly"] == "true"
            assert "create_branch" not in request.headers["x-mcp-tools"]
            observed.append(request.method)
            return await asgi.handle_async_request(request)

        monkeypatch.setattr(
            "repopilot.github.client.OfficialTransport",
            lambda: httpx2.MockTransport(respond),
        )
        async with app.router.lifespan_context(app):
            report = await probe(settings(github_mcp_token="test-secret"), "test")
        assert report["status"] == "passed"
        assert report["successful_calls"] == 1
        assert report["remote_writes"] == 0
        assert "test-secret" not in json.dumps(report)
        assert "POST" in observed
        assert not any(method not in {"GET", "POST", "DELETE"} for method in observed)

    with caplog.at_level(logging.DEBUG):
        anyio.run(run)
    assert "test-secret" not in caplog.text


def test_settings_error_string_does_not_expose_token(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError) as caught:
        Settings(_env_file=None, github_mcp_token="test-secret")
    assert "test-secret" not in str(caught.value)


def test_discovery_denies_writes_even_with_readonly_annotation():
    async def run():
        client = fake_client([tool(), tool("create_branch")])
        reader = GitHubReadClient(client, settings())
        with pytest.raises(GitHubMCPError, match="discovery_denied"):
            await reader.discover()
        client.call_tool.assert_not_called()

    anyio.run(run)


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "object", "$ref": "https://example.com/schema"},
        {"type": "object", "$dynamicRef": "https://example.com/schema"},
        {"type": "object", "$recursiveRef": "https://example.com/schema"},
        {"type": "string"},
    ],
)
def test_remote_schema_references_and_invalid_roots_denied(schema):
    async def run():
        reader = GitHubReadClient(fake_client([tool(schema=schema)]), settings())
        with pytest.raises(GitHubMCPError, match="schema_denied"):
            await reader.discover()

    anyio.run(run)


def test_paginated_discovery_rejects_cursor_cycle():
    async def run():
        client = fake_client()
        client.list_tools.side_effect = [
            SimpleNamespace(tools=[tool()], next_cursor="repeat"),
            SimpleNamespace(tools=[], next_cursor="repeat"),
        ]
        with pytest.raises(GitHubMCPError, match="discovery_cycle"):
            await GitHubReadClient(client, settings()).discover()

    anyio.run(run)


def test_permissions_paths_revision_and_arguments_checked_before_call():
    async def run():
        client = fake_client(
            [tool(), tool("get_file_contents"), tool("issue_read"), tool("get_commit")]
        )
        reader = GitHubReadClient(
            client, settings(github_mcp_allowed_repositories=["juice-gift/test"])
        )
        await reader.discover()
        for operation in (
            reader.commit("elsewhere/repo", "main"),
            reader.file("juice-gift/test", "fees.py", "main"),
            reader.file("juice-gift/test", "../fees.py", "a" * 40),
            reader.file("juice-gift/test", ".env", "a" * 40),
            reader.issue("juice-gift/test", True),
            reader._call("create_branch", {"owner": "juice-gift", "repo": "test"}),
            reader._call(
                "issue_read",
                {"owner": "juice-gift", "repo": "test", "method": "update"},
            ),
        ):
            with pytest.raises(GitHubMCPError):
                await operation
        client.call_tool.assert_not_called()
        await reader.file("Juice-Gift/Test", "fees.py", "a" * 40)
        client.call_tool.assert_awaited_once_with(
            "get_file_contents",
            {
                "owner": "juice-gift",
                "repo": "test",
                "path": "fees.py",
                "ref": "a" * 40,
            },
        )

    anyio.run(run)


def test_discovered_argument_schema_enforced_and_remote_failure_redacted():
    async def run():
        client = fake_client(
            [tool(schema={"type": "object", "required": ["unrecognized_argument"]})]
        )
        reader = GitHubReadClient(client, settings())
        await reader.discover()
        with pytest.raises(GitHubMCPError, match="arguments_invalid"):
            await reader.identity()
        client.call_tool.assert_not_called()
        client = fake_client()
        client.call_tool.side_effect = RuntimeError("test-secret-in-remote-error")
        reader = GitHubReadClient(client, settings())
        await reader.discover()
        with pytest.raises(GitHubMCPError) as caught:
            await reader.identity()
        assert str(caught.value) == "transport_failure"
        assert caught.value.__suppress_context__

    anyio.run(run)


def test_results_redact_credential_and_error_or_large_results_are_rejected():
    async def run():
        client = fake_client()
        client.call_tool.return_value = CallToolResult(
            content=[TextContent(type="text", text="test-secret")]
        )
        reader = GitHubReadClient(
            client, settings(github_mcp_token=SecretStr("test-secret"))
        )
        await reader.discover()
        assert "test-secret" not in json.dumps((await reader.identity()).data)
        client.call_tool.return_value = CallToolResult(
            is_error=True, content=[TextContent(type="text", text="test-secret")]
        )
        with pytest.raises(GitHubMCPError, match="tool_failed"):
            await reader.identity()
        client.call_tool.return_value = CallToolResult(
            content=[TextContent(type="text", text="x" * 128_001)]
        )
        with pytest.raises(GitHubMCPError, match="result_limit"):
            await reader.identity()
        reader.calls = 24
        with pytest.raises(GitHubMCPError, match="call_limit"):
            await reader.identity()

    anyio.run(run)


def test_transport_does_not_send_credential_to_redirect_or_foreign_endpoint():
    async def run():
        transport = OfficialTransport()
        called = []

        async def respond(request):
            called.append(str(request.url))
            return httpx2.Response(
                307, headers={"location": "https://example.com/steal"}
            )

        await transport._transport.aclose()
        transport._transport = httpx2.MockTransport(respond)
        async with httpx2.AsyncClient(
            transport=transport, follow_redirects=True
        ) as client:
            with pytest.raises(GitHubMCPError, match="endpoint_denied"):
                await client.post(
                    ENDPOINT, headers={"Authorization": "Bearer test-secret"}
                )
        assert called == [ENDPOINT]

    anyio.run(run)


def test_stream_size_and_compression_limits():
    async def run():
        stream = _BoundedStream(httpx2.ByteStream(b"x" * 1_048_577))
        with pytest.raises(GitHubMCPError, match="response_limit"):
            async for _ in stream:
                pass
        transport = OfficialTransport()
        await transport._transport.aclose()
        transport._transport = httpx2.MockTransport(
            lambda request: httpx2.Response(200, headers={"content-encoding": "gzip"})
        )
        async with httpx2.AsyncClient(transport=transport) as client:
            with pytest.raises(GitHubMCPError, match="encoding_denied"):
                await client.get(ENDPOINT)

    anyio.run(run)


def test_sdk_logs_are_suppressed_only_in_private_context(caplog):
    logger = logging.getLogger("mcp.client.streamable_http")
    with caplog.at_level(logging.DEBUG):
        with private_transport_logs():
            logger.error("test-secret-in-untrusted-response")
        logger.warning("normal-log-outside-context")
    assert "test-secret" not in caplog.text
    assert "normal-log-outside-context" in caplog.text


def test_authentication_error_classification_does_not_include_headers():
    request = httpx2.Request(
        "POST", ENDPOINT, headers={"Authorization": "Bearer test-secret"}
    )
    for status, code in ((401, "authentication_failed"), (403, "permission_denied")):
        exc = httpx2.HTTPStatusError(
            "test-secret", request=request, response=httpx2.Response(status)
        )
        assert str(_safe_error(exc)) == code
