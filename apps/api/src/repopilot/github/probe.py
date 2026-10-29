"""Actual official-server connection/identity check; emits no raw tool output."""

import argparse
import json
from importlib.metadata import version

import anyio
from pydantic import ValidationError

from repopilot.config import Settings
from repopilot.github.client import GitHubMCPError, ToolData, connect_github_readonly


def object_payload(result: ToolData) -> dict[str, object]:
    structured = result.data.get("structured_content")
    if isinstance(structured, dict):
        return structured
    content = result.data.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    parsed = json.loads(str(block.get("text", "")))
                except (ValueError, TypeError):
                    continue
                if isinstance(parsed, dict):
                    return parsed
    raise GitHubMCPError("identity_unrecognized")


async def probe(settings: Settings, expected_login: str) -> dict[str, object]:
    async with connect_github_readonly(settings) as reader:
        result = object_payload(await reader.identity())
        if result.get("login") != expected_login:
            raise GitHubMCPError("identity_mismatch")
        return {
            "status": "passed",
            "measurement": "actual official GitHub MCP discovery and get_me",
            "sdk_version": version("mcp"),
            **reader.connection_evidence,
            "identity_matches_expected": True,
            "successful_calls": reader.calls,
            "repository_reads": 0,
            "remote_writes": 0,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-login", required=True)
    args = parser.parse_args()
    try:
        report = anyio.run(probe, Settings(), args.expected_login)
    except GitHubMCPError as exc:
        # No raw exception/traceback, HTTP body/header or Token is printed.
        print(json.dumps({"status": "unverified", "code": exc.code}))
        raise SystemExit(1) from None
    except ValidationError:
        print(json.dumps({"status": "unverified", "code": "configuration_invalid"}))
        raise SystemExit(1) from None
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
