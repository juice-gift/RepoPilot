"""Persist deterministic repairs and awaiting-review proposals for actual MCP bindings.

No approval, GitHub branch/commit/PR creation, or remote write capability is used.
"""

import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from repopilot.config import Settings
from repopilot.db.models import GitHubIssueSnapshot
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.embeddings.providers import create_embedding_provider
from repopilot.github.proposals import checked_plan, prepare_proposal
from repopilot.github.resolution import resolve_bound_issue
from repopilot.rag.tool_calling import AgentTurn, ToolCall
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxExecutor

ROOT = Path(__file__).resolve().parents[2]


class ReviewedScript:
    provider_name, model_name = "scripted", "deterministic-not-llm"

    def __init__(self, profile):
        path = next(iter(profile.editable_paths))
        start = 3300 if "more-itertools" in profile.case_id else 1
        old, new = (("    windows = windowed(it, window_size)", "    windows = windowed(it, window_size, fillvalue=_marker)")
                    if "more-itertools" in profile.case_id else
                    ("            if age > max_age:", "            if age < 0 or age > max_age:"))

        def call(name, args, step):
            return AgentTurn(tool_calls=(ToolCall(str(step), name, json.dumps(args)),))

        self.turns = iter([
            call("read_file", {"path": path, "start_line": start, "end_line": start + 150}, 1),
            call("submit_plan", {"expected_revision": 0, "decision": "repair", "summary": "Repair approved historical issue",
                                 "steps": ["Reproduce, patch, independently verify"], "files": [path]}, 2),
            call("run_tests", {"expected_revision": 0}, 3),
            call("apply_patch", {"expected_revision": 0, "edits": [{"path": path, "old_text": old, "new_text": new}]}, 4),
            call("run_tests", {"expected_revision": 1}, 5),
            AgentTurn(text="Deterministic repair verified. Human review and separate publication authority required."),
        ])

    def complete(self, **kwargs):
        return next(self.turns)


def main() -> None:
    registry = ROOT / "apps/api/evaluation/trusted_python/profiles.json"
    settings = Settings(trusted_profile_registry=registry,
                        trusted_profile_registry_sha256=hashlib.sha256(registry.read_bytes()).hexdigest(),
                        github_mcp_allowed_repositories=["pallets/itsdangerous", "more-itertools/more-itertools"],
                        github_write_allowed_repositories=[], embedding_provider="deterministic")
    engine = create_database_engine(settings.database_url)
    report = {"mode": "deterministic Agent; actual MCP-bound source, DB and Docker", "remote_writes": 0, "cases": []}
    try:
        with create_database_session_factory(engine)() as session:
            for profile_id in ("trusted-itsdangerous", "trusted-more-itertools"):
                profile = load_profile(profile_id, registry_path=registry, registry_digest=settings.trusted_profile_registry_sha256)
                binding = session.scalar(select(GitHubIssueSnapshot).where(
                    GitHubIssueSnapshot.repository_full_name == profile.repository,
                    GitHubIssueSnapshot.commit_sha == profile.commit_sha,
                    GitHubIssueSnapshot.profile == profile_id))
                if binding is None:
                    raise ValueError("Run the actual read-only importer first")
                run = resolve_bound_issue(session, settings, binding_id=binding.id,
                    provider=ReviewedScript(profile), executor=SandboxExecutor(profile.image_id, timeout_seconds=40),
                    embedding_factory=lambda: create_embedding_provider(settings))
                row = prepare_proposal(session, settings, run.id)
                plan = checked_plan(session, settings, row)
                report["cases"].append({"binding_id": binding.id, "run_id": run.id, "result_hash": run.result_hash,
                    "result": run.result, "proposal_id": row.id, "proposal_hash": row.plan_hash,
                    "state": row.state, "plan": plan.model_dump(mode="json"),
                    "publication_limitations": ["Public historical upstream is not an owner-controlled private main baseline",
                                                "No remote write allowlist or approval granted"]})
                (ROOT / "docs/evaluation/pre-v8-bound-proposals.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                print(json.dumps({"profile": profile_id, "repair_status": run.result["repair_status"], "proposal_id": row.id, "state": row.state}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
