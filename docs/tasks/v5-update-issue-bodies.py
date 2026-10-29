"""Owner-authorized one-off fixture preparation. Never a product Agent tool.

From apps/api: $env:PYTHONPATH='src'; uv run python ../../docs/tasks/v5-update-issue-bodies.py --apply
Without --apply this performs only the read-only preparation check.
Only the three fixed Issue bodies can be changed; files, branches and PRs cannot.
"""

import argparse
import json

import anyio
import httpx2
from jsonschema import Draft202012Validator
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.github.client import (
    ENDPOINT,
    GitHubMCPError,
    OfficialTransport,
    ToolData,
    private_transport_logs,
)
from repopilot.github.fixture_audit import audit_fixture
from repopilot.github.probe import object_payload
from repopilot.resolution.profiles import load_profile

REPOSITORY = "juice-gift/repopilot-v5-sandbox"
BASELINE = "b4279c8b4d862817e6778caa5f87da91d29ed2b7"
CASES = ("fee-days", "dispatch-preconditions", "ambiguous-cap")


async def audit(settings: Settings) -> dict[str, object]:
    return await audit_fixture(
        settings,
        repository=REPOSITORY,
        expected_commit=BASELINE,
        issue_numbers=(1, 2, 3),
        expected_login="juice-gift",
    )


async def prepare(apply: bool) -> None:
    settings = Settings(github_mcp_allowed_repositories=[REPOSITORY])
    before = await audit(settings)
    checks = before["checks"]
    if not all(
        value for key, value in checks.items() if key != "issue_contracts_match"
    ):
        raise GitHubMCPError("fixture_or_baseline_changed_no_writes")
    if not apply:
        print(json.dumps({"mode": "read_only", "checks": checks}))
        return
    # The existing read-only product client is never given write tools.
    with private_transport_logs():
        async with httpx2.AsyncClient(
            headers={
                "Authorization": "Bearer "
                + settings.github_mcp_token.get_secret_value(),
                "X-MCP-Tools": "get_me,issue_read,issue_write",
                "Accept-Encoding": "identity",
            },
            transport=OfficialTransport(),
            timeout=30,
            trust_env=False,
        ) as http:
            async with Client(
                streamable_http_client(ENDPOINT, http_client=http),
                cache=None,
                read_timeout_seconds=30,
                input_required_max_rounds=0,
            ) as client:
                schemas = {
                    tool.name: tool.input_schema
                    for tool in (await client.list_tools()).tools
                }

                async def call(
                    name: str, arguments: dict[str, object]
                ) -> dict[str, object]:
                    Draft202012Validator(schemas[name]).validate(arguments)
                    response = await client.call_tool(name, arguments)
                    if response.is_error:
                        raise GitHubMCPError(
                            "issue_operation_denied_check_PAT_Issues_write"
                        )
                    return object_payload(
                        ToolData(name, json.loads(response.model_dump_json()))
                    )

                if (await call("get_me", {})).get("login") != "juice-gift":
                    raise GitHubMCPError("identity_mismatch")
                for number, case in enumerate(CASES, 1):
                    scope = {
                        "owner": "juice-gift",
                        "repo": "repopilot-v5-sandbox",
                        "issue_number": number,
                    }
                    expected = load_profile(case).issue
                    current = (await call("issue_read", {**scope, "method": "get"}))[
                        "issue"
                    ]
                    if (
                        current["html_url"]
                        != f"https://github.com/{REPOSITORY}/issues/{number}"
                    ):
                        raise GitHubMCPError("issue_identity_mismatch")
                    if current.get("body") != expected:
                        await call(
                            "issue_write",
                            {**scope, "method": "update", "body": expected},
                        )
                    actual = (await call("issue_read", {**scope, "method": "get"}))[
                        "issue"
                    ]
                    if actual.get("body") != expected:
                        raise GitHubMCPError("issue_body_not_verified")
                    print(f"Issue #{number}: frozen body verified")
    after = await audit(settings)
    output = REPOSITORY_ROOT / "docs/evaluation/v5-fixture-final-audit.json"
    output.write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    if after["status"] != "passed":
        raise GitHubMCPError("final_fixture_audit_failed")
    print("All fixture checks passed; main=" + BASELINE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        anyio.run(prepare, args.apply)
    except GitHubMCPError as exc:
        print("Stopped: " + exc.code)
        raise SystemExit(1) from None
    except Exception:  # noqa: BLE001 - never print credential-bearing SDK/config errors
        print(
            "Stopped: preparation failure; reconcile actual Issue bodies before retry"
        )
        raise SystemExit(1) from None
