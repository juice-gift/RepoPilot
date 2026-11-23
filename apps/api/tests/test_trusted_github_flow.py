"""Deterministic remote evidence, real DB/index/Agent loop/Docker, no remote writes."""

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.models import GitHubPublication, GitHubResolutionRun, Repository
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.embeddings.providers import create_embedding_provider
from repopilot.github.binding import persist_binding
from repopilot.github.client import GitHubMCPError
from repopilot.github.git_api import require_write_scope
from repopilot.github.proposals import approve_proposal, checked_plan, prepare_proposal
from repopilot.github.resolution import resolve_bound_issue
from repopilot.rag.tool_calling import AgentTurn, ToolCall
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxExecutor

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1"
    or os.getenv("RUN_TRUSTED_PYTHON_TESTS") != "1",
    reason="requires live DB and approved trusted Python sandbox",
)


def test_real_python_bound_repair_and_exact_proposal_approval():
    root = REPOSITORY_ROOT / "apps/api/evaluation/trusted_python"
    registry = Path(
        os.environ.get("TEST_TRUSTED_PROFILE_REGISTRY", str(root / "profiles.json"))
    )
    settings = Settings(
        trusted_profile_registry=registry,
        trusted_profile_registry_sha256=hashlib.sha256(
            registry.read_bytes()
        ).hexdigest(),
        github_mcp_allowed_repositories=["pallets/itsdangerous"],
        github_write_allowed_repositories=[],
        embedding_provider="deterministic",
    )
    profile = load_profile(
        "trusted-itsdangerous",
        registry_path=registry,
        registry_digest=settings.trusted_profile_registry_sha256,
    )
    sources = {
        p: (root / "itsdangerous/repository" / p).read_text(encoding="utf-8")
        for p in profile.expected_sources
    }
    remote_id = int(uuid4().hex[:12], 16)
    audit = {
        "status": "passed",
        "checks": {"fake_remote": True},
        "repository_id": remote_id,
        "repository": profile.repository,
        "actual_commit": profile.commit_sha,
        "issues": [
            {
                "case": profile.case_id,
                "number": profile.issue_number,
                "matches_frozen_contract": True,
            }
        ],
    }
    path = "src/itsdangerous/timed.py"

    def call(name, arguments, step):
        return AgentTurn(tool_calls=(ToolCall(str(step), name, json.dumps(arguments)),))

    class Scripted:
        provider_name, model_name = "scripted", "not-llm-evidence"

        def __init__(self):
            self.turns = iter(
                [
                    call("read_file", {"path": path}, 1),
                    call(
                        "submit_plan",
                        {
                            "expected_revision": 0,
                            "decision": "repair",
                            "summary": "Reject negative timestamp ages",
                            "steps": ["Reproduce and repair age validation"],
                            "files": [path],
                        },
                        2,
                    ),
                    call("run_tests", {"expected_revision": 0}, 3),
                    call(
                        "apply_patch",
                        {
                            "expected_revision": 0,
                            "edits": [
                                {
                                    "path": path,
                                    "old_text": "            if age > max_age:",
                                    "new_text": "            if age < 0 or age > max_age:",
                                }
                            ],
                        },
                        4,
                    ),
                    call("run_tests", {"expected_revision": 1}, 5),
                    AgentTurn(text="Deterministic historical repair verified."),
                ]
            )

        def complete(self, **kwargs):
            return next(self.turns)

    engine = create_database_engine(settings.database_url)
    factory = create_database_session_factory(engine)
    run_id = None
    try:
        with factory() as session:
            binding = persist_binding(
                session, audit=audit, sources=sources, approved_profiles=[profile]
            )[0]
            assert binding.issue_body == profile.bound_issue
            run = resolve_bound_issue(
                session,
                settings,
                binding_id=binding.id,
                provider=Scripted(),
                executor=SandboxExecutor(profile.image_id, timeout_seconds=40),
                embedding_factory=lambda: create_embedding_provider(settings),
            )
            run_id = run.id
            assert run.result["repair_status"] == "verified_repair"
            row = prepare_proposal(session, settings, run.id)
            plan = checked_plan(session, settings, row)
            assert plan.baseline_tree_sha == profile.baseline_tree_sha
            assert plan.changed_paths == [path] and set(plan.files) == {path}
            assert plan.test_passed == 8 and plan.tested_revision == 1
            assert path in plan.diff
            with pytest.raises(GitHubMCPError, match="approval_mismatch"):
                approve_proposal(session, settings, row.id, "wrong", "wrong")
            session.rollback()
            approve_proposal(
                session,
                settings,
                row.id,
                row.plan_hash,
                f"APPROVE {row.id}:{row.plan_hash}",
            )
            with pytest.raises(GitHubMCPError, match="publication_not_authorized"):
                require_write_scope(settings, plan, row.approved_hash)
            # Test evidence from an altered approved policy cannot authorize a proposal.
            run.result = {**run.result, "revision": 2}
            session.commit()
            with pytest.raises(GitHubMCPError, match="run_not_verified"):
                checked_plan(session, settings, row)
    finally:
        with factory() as session:
            if run_id:
                session.execute(
                    delete(GitHubPublication).where(GitHubPublication.run_id == run_id)
                )
                session.execute(
                    delete(GitHubResolutionRun).where(GitHubResolutionRun.id == run_id)
                )
            session.execute(
                delete(Repository).where(
                    Repository.local_path
                    == f"github://github.com/repositories/{remote_id}"
                )
            )
            session.commit()
        engine.dispose()
