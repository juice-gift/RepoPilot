"""Export exact persisted publication plans and real MCP read-only preflight.

This command cannot approve or publish. Run from apps/api with PYTHONPATH=src.
"""

import argparse
import json
from pathlib import Path

import anyio

from repopilot.config import Settings
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.github.client import GitHubMCPError
from repopilot.github.git_api import read_git_baseline
from repopilot.github.pr_client import inspect_pr_support
from repopilot.github.proposals import checked_plan, prepare_proposal
from repopilot.github.publication import (
    readonly_preflight,
    verify_ref,
    verify_repository,
)


async def export_review(repository: str, runs: list[str], output: Path) -> None:
    settings = Settings(
        github_mcp_allowed_repositories=[repository],
        github_write_allowed_repositories=[],
    )
    engine = create_database_engine(settings.database_url)
    report = {
        "measurement": "actual MCP prepublication reads; no remote writes or approval",
        "repository": repository,
        "remote_writes": 0,
        "proposals": [],
    }
    try:
        with create_database_session_factory(engine)() as session:
            for run in runs:
                row = prepare_proposal(session, settings, run)
                if row.approved_hash is not None or row.state != "awaiting_approval":
                    raise GitHubMCPError("review_requires_unapproved_proposal")
                plan = checked_plan(session, settings, row)
                git = await read_git_baseline(settings, plan)
                verify_repository(git["repository"], plan)
                verify_ref(git["base_ref"], "main", plan.base_sha)
                commit = git["base_commit"]
                if (
                    commit is None
                    or commit.get("sha") != plan.base_sha
                    or commit.get("tree", {}).get("sha") != plan.baseline_tree_sha
                    or git["head_ref"] is not None
                ):
                    raise GitHubMCPError("prepublication_git_baseline_mismatch")
                report["proposals"].append(
                    {
                        "id": row.id,
                        "plan_hash": row.plan_hash,
                        "state": row.state,
                        "approved": False,
                        "git_readonly": {
                            "baseline_tree_sha": plan.baseline_tree_sha,
                            "exact_baseline_tree_verified": True,
                            "head_absent": True,
                            "reported_push_role": True,
                            "pat_write_permission": "not exercised before explicit approval",
                            "remote_writes": 0,
                        },
                        "plan": plan.model_dump(mode="json"),
                        "readonly_preflight": await readonly_preflight(settings, plan),
                        "pr_support": await inspect_pr_support(settings, plan),
                    }
                )
    finally:
        engine.dispose()
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "report": str(output),
                "proposals": len(report["proposals"]),
                "remote_writes": 0,
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        anyio.run(export_review, args.repository, args.run, args.output)
    except GitHubMCPError as exc:
        raise SystemExit(exc.code) from None


if __name__ == "__main__":
    main()
