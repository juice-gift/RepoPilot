import os
from pathlib import Path

import pytest
from sqlalchemy import delete, select

from repopilot.agent.tools import RunScope
from repopilot.config import Settings
from repopilot.db.models import Repository, SnapshotFile
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.ingestion.service import ingest_repository
from repopilot.resolution.patch import PatchArguments, PatchEngine, actual_diff
from repopilot.resolution.workspace import Workspace, WorkspaceError, snapshot_sources

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires migrated PostgreSQL"
)


def test_saved_snapshot_workspace_isolation_and_integrity(tmp_path: Path):
    original = tmp_path / "app.py"
    original.write_bytes(b"value = 1\n")
    engine = create_database_engine(Settings().database_url)
    factory = create_database_session_factory(engine)
    repository_id = None
    try:
        with factory() as session:
            ingested = ingest_repository(
                session, requested_path=str(tmp_path), allowed_root=tmp_path
            )
            repository_id = ingested.repository.id
            scope = RunScope(repository_id, ingested.snapshot.id)
            original.write_bytes(b"value = 999\n")
            with Workspace(scope, snapshot_sources(session, scope)) as workspace:
                assert workspace.read("app.py") == "value = 1\n"
                PatchEngine(workspace, frozenset({"app.py"})).apply(
                    PatchArguments(
                        expected_revision=0,
                        edits=[
                            {
                                "path": "app.py",
                                "old_text": "value = 1",
                                "new_text": "value = 2",
                            }
                        ],
                    ),
                    attempt=1,
                )
                assert workspace.read("app.py") == "value = 2\n"
                assert "-value = 1\n+value = 2\n" in actual_diff(workspace)
                assert original.read_bytes() == b"value = 999\n"
                saved = session.scalar(
                    select(SnapshotFile).where(
                        SnapshotFile.snapshot_id == scope.snapshot_id
                    )
                )
                assert saved.content == "value = 1\n"
                saved.content = "corrupt\n"
                session.flush()
                with pytest.raises(WorkspaceError):
                    Workspace(scope, snapshot_sources(session, scope))
    finally:
        if repository_id:
            with factory() as session:
                session.execute(
                    delete(Repository).where(Repository.id == repository_id)
                )
                session.commit()
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_SANDBOX_TESTS") != "1", reason="requires prepared Docker test image"
)
def test_live_snapshot_resolution_repairs_actual_failure_and_preserves_baseline(
    tmp_path: Path,
):
    from test_agent_runner import ScriptedProvider, call
    from test_resolution_runner import fee_patch, plan

    from repopilot.agent.tools import ToolRegistry
    from repopilot.embeddings.providers import DeterministicEmbeddingProvider
    from repopilot.indexing.service import index_snapshot
    from repopilot.intelligence.service import index_structure
    from repopilot.rag.tool_calling import AgentTurn
    from repopilot.resolution.models import ResolutionRequest
    from repopilot.resolution.profiles import GOLDEN_ROOT
    from repopilot.resolution.sandbox import SandboxExecutor, docker
    from repopilot.resolution.service import resolve_snapshot

    original = {p.name: p.read_bytes() for p in (GOLDEN_ROOT / "repository").iterdir()}
    target = tmp_path / "golden-source"
    target.mkdir()
    for name, data in original.items():
        (target / name).write_bytes(data)
    engine = create_database_engine(Settings().database_url)
    factory = create_database_session_factory(engine)
    repository_id = None
    try:
        with factory() as session:
            ingested = ingest_repository(
                session,
                requested_path=str(target),
                allowed_root=tmp_path,
            )
            repository_id = ingested.repository.id
            scope = RunScope(repository_id, ingested.snapshot.id)
            before = snapshot_sources(session, scope)
            index_structure(
                session,
                repository_id=scope.repository_id,
                snapshot_id=scope.snapshot_id,
            )
            index_snapshot(
                session,
                repository_id=scope.repository_id,
                snapshot_id=scope.snapshot_id,
                provider=DeterministicEmbeddingProvider(),
            )
            wrong = "min(max(overdue_days - 2, 0), 30)"
            result = resolve_snapshot(
                ResolutionRequest(
                    repository_id=scope.repository_id,
                    snapshot_id=scope.snapshot_id,
                    profile="fee-days",
                    issue="Charge every overdue day, capped at 30.",
                ),
                session=session,
                baseline=ToolRegistry(
                    session, scope, embedding_factory=DeterministicEmbeddingProvider
                ),
                executor=SandboxExecutor(
                    docker(
                        "image", "inspect", "repopilot-tests:v4", "--format", "{{.Id}}"
                    ).strip()
                ),
                provider=ScriptedProvider(
                    call("read_file", {"path": "fees.py"}, "read"),
                    call("retrieve_context", {"query": "late_fee"}, "retrieval"),
                    call("submit_plan", plan(), "plan"),
                    call("run_tests", {"expected_revision": 0}, "baseline"),
                    call("apply_patch", fee_patch(new=wrong), "wrong"),
                    call("run_tests", {"expected_revision": 1}, "failure"),
                    call("apply_patch", fee_patch(1, old=wrong), "repair"),
                    call("search_symbol", {"query": "late_fee"}, "stale"),
                    call("read_file", {"path": "fees.py"}, "current"),
                    call("run_tests", {"expected_revision": 2}, "verify"),
                    AgentTurn(
                        text="Scripted repair verified against independent Golden tests."
                    ),
                ),
            )
            assert (
                result.repair_status == "verified_repair" and result.workspace_cleaned
            )
            assert [t.exit_code for t in result.test_results] == [1, 1, 0]
            assert result.test_results[-1].observed_passed == 8
            assert (
                result.trace[7].observation.payload["stale_after_modifications"] is True
            )
            assert result.trace[8].observation.payload["revision"] == 2
            assert snapshot_sources(session, scope) == before
            assert {
                p.name: p.read_bytes() for p in (GOLDEN_ROOT / "repository").iterdir()
            } == original
            assert {p.name: p.read_bytes() for p in target.iterdir()} == original
    finally:
        if repository_id:
            with factory() as session:
                session.execute(
                    delete(Repository).where(Repository.id == repository_id)
                )
                session.commit()
        engine.dispose()
