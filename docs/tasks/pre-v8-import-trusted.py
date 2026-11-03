"""Actual approved public-repository MCP reads and local binding only. No remote writes."""

import hashlib
import json
from pathlib import Path

import anyio

from repopilot.config import Settings
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.github.binding import import_trusted_issue
from repopilot.github.client import GitHubMCPError

ROOT = Path(__file__).resolve().parents[2]


async def main() -> None:
    registry = ROOT / "apps/api/evaluation/trusted_python/profiles.json"
    settings = Settings(
        trusted_profile_registry=registry,
        trusted_profile_registry_sha256=hashlib.sha256(registry.read_bytes()).hexdigest(),
        github_mcp_allowed_repositories=["pallets/itsdangerous", "more-itertools/more-itertools"],
        github_write_allowed_repositories=[],
    )
    engine = create_database_engine(settings.database_url)
    factory = create_database_session_factory(engine)
    report = {"measurement": "actual official GitHub MCP reads; local DB binding", "remote_writes": 0, "cases": []}
    try:
        for profile in ("trusted-itsdangerous", "trusted-more-itertools"):
            with factory() as session:
                try:
                    row = await import_trusted_issue(session, settings, profile_id=profile)
                    result = {"profile": profile, "state": "bound", "binding_id": row.id,
                              "repository": row.repository_full_name, "commit": row.commit_sha,
                              "snapshot_id": row.snapshot_id, "audit": row.audit}
                except GitHubMCPError as error:
                    result = {"profile": profile, "state": "failed", "failure": error.code}
                report["cases"].append(result)
                (ROOT / "docs/evaluation/pre-v8-trusted-import.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                print(json.dumps({k: v for k, v in result.items() if k != "audit"}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    anyio.run(main)
