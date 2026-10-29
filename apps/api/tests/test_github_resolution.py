import os

import pytest
from sqlalchemy import delete, select
from test_github_binding import fixture_data

from repopilot.config import Settings
from repopilot.db.models import GitHubResolutionRun, Repository
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.evaluation.resolution import ScriptedResolutionProvider
from repopilot.github.binding import persist_binding
from repopilot.github.client import GitHubMCPError
from repopilot.github.resolution import resolve_bound_issue, result_hash
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxExecutor, docker

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires PostgreSQL"
)


def test_bound_resolution_denials_and_persistent_failure(monkeypatch):
    audit, sources = fixture_data()
    engine = create_database_engine(Settings().database_url)
    factory = create_database_session_factory(engine)
    key = f"github://github.com/repositories/{audit['repository_id']}"
    binding_ids = []
    try:
        with factory() as session:
            rows = persist_binding(session, audit=audit, sources=sources)
            binding_ids = [r.id for r in rows]
            args = {
                "binding_id": rows[0].id,
                "provider": ScriptedResolutionProvider(load_profile("fee-days")),
                "executor": SandboxExecutor("sha256:" + "0" * 64),
                "embedding_factory": DeterministicEmbeddingProvider,
            }
            with pytest.raises(GitHubMCPError, match="binding_denied"):
                resolve_bound_issue(
                    session, Settings(github_mcp_allowed_repositories=[]), **args
                )
            config = Settings(github_mcp_allowed_repositories=[audit["repository"]])

            def fail(*args, **kwargs):
                raise RuntimeError("do-not-record-sensitive-detail")

            monkeypatch.setattr("repopilot.github.resolution.index_structure", fail)
            with pytest.raises(GitHubMCPError, match="resolution_failed"):
                resolve_bound_issue(session, config, **args)
            run = session.scalar(
                select(GitHubResolutionRun).where(
                    GitHubResolutionRun.binding_id == rows[0].id
                )
            )
            assert run.state == "failed" and run.failure == "resolution_failed"
            assert run.result is None
    finally:
        with factory() as session:
            session.execute(
                delete(GitHubResolutionRun).where(
                    GitHubResolutionRun.binding_id.in_(binding_ids)
                )
            )
            session.execute(delete(Repository).where(Repository.local_path == key))
            session.commit()
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_SANDBOX_TESTS") != "1", reason="requires controlled Docker image"
)
def test_bound_issue_real_docker_repair_is_saved_with_exact_result_hash():
    audit, sources = fixture_data()
    engine = create_database_engine(Settings().database_url)
    factory = create_database_session_factory(engine)
    key = f"github://github.com/repositories/{audit['repository_id']}"
    binding_ids = []
    try:
        with factory() as session:
            bindings = persist_binding(session, audit=audit, sources=sources)
            binding_ids = [r.id for r in bindings]
            image = docker(
                "image", "inspect", "repopilot-tests:v4", "--format", "{{.Id}}"
            ).strip()
            run = resolve_bound_issue(
                session,
                Settings(github_mcp_allowed_repositories=[audit["repository"]]),
                binding_id=bindings[0].id,
                provider=ScriptedResolutionProvider(load_profile("fee-days")),
                executor=SandboxExecutor(image),
                embedding_factory=DeterministicEmbeddingProvider,
            )
            assert run.state == "completed"
            assert run.result["repair_status"] == "verified_repair"
            assert run.result["workspace_cleaned"] is True
            assert run.result_hash == result_hash(run.result)
            assert run.binding_id == bindings[0].id
    finally:
        with factory() as session:
            session.execute(
                delete(GitHubResolutionRun).where(
                    GitHubResolutionRun.binding_id.in_(binding_ids)
                )
            )
            session.execute(delete(Repository).where(Repository.local_path == key))
            session.commit()
        engine.dispose()
