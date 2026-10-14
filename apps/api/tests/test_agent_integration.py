import json
import os
from pathlib import Path

import pytest
from sqlalchemy import delete, select
from test_agent_runner import ScriptedProvider, call

from repopilot.agent.models import AgentRequest
from repopilot.agent.runner import run_investigation
from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.config import Settings
from repopilot.db.models import Repository, SnapshotFile
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.indexing.service import index_snapshot
from repopilot.ingestion.service import ingest_repository
from repopilot.intelligence.service import index_structure
from repopilot.rag.tool_calling import AgentTurn, DeterministicAgentProvider

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires migrated PostgreSQL"
)


def test_all_tools_read_saved_snapshot_and_enforce_both_ids(tmp_path: Path):
    source = tmp_path / "app.py"
    source.write_text('def run():\n    return "100%_literal"\n', encoding="utf-8")
    engine = create_database_engine(Settings().database_url)
    factory = create_database_session_factory(engine)
    repository_ids: list[int] = []
    try:
        with factory() as session:
            first = ingest_repository(
                session, requested_path=str(tmp_path), allowed_root=tmp_path
            )
            repository_ids.append(first.repository.id)
            scope = RunScope(first.repository.id, first.snapshot.id)
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
            source.write_text("def newer():\n    return 99\n", encoding="utf-8")
            second = ingest_repository(
                session, requested_path=str(tmp_path), allowed_root=tmp_path
            )
            other_path = tmp_path / "other"
            other_path.mkdir()
            (other_path / "app.py").write_text("def outsider(): pass", encoding="utf-8")
            other = ingest_repository(
                session, requested_path=str(other_path), allowed_root=tmp_path
            )
            repository_ids.append(other.repository.id)
            registry = ToolRegistry(
                session, scope, embedding_factory=DeterministicEmbeddingProvider
            )
            cases = [
                ("list_files", {}, "app.py"),
                (
                    "read_file",
                    {"path": "app.py", "start_line": 2, "end_line": 2},
                    "100%_literal",
                ),
                ("search_code", {"query": "%_"}, "100%_literal"),
                ("search_symbol", {"query": "run"}, "run"),
                ("retrieve_context", {"query": "run 100%_literal"}, "100%_literal"),
            ]
            for name, args, expected in cases:
                result = registry.execute(name, json.dumps(args), evidence_prefix="E1")
                assert result.observation.status == "ok"
                assert expected in result.observation.model_dump_json()
                assert "newer" not in result.observation.model_dump_json()
                assert "outsider" not in result.observation.model_dump_json()
                invalid = ToolRegistry(
                    session,
                    RunScope(other.repository.id, scope.snapshot_id),
                    embedding_factory=DeterministicEmbeddingProvider,
                )
                assert (
                    invalid.execute(
                        name, json.dumps(args), evidence_prefix="E1"
                    ).observation.error_code
                    == "snapshot_not_found"
                )
            fresh = ToolRegistry(
                session,
                RunScope(scope.repository_id, second.snapshot.id),
                embedding_factory=DeterministicEmbeddingProvider,
            )
            assert (
                "newer"
                in fresh.execute(
                    "read_file", '{"path":"app.py"}', evidence_prefix="E1"
                ).model_dump_json()
            )
            assert (
                fresh.execute(
                    "search_symbol", '{"query":"newer"}', evidence_prefix="E1"
                ).observation.error_code
                == "index_not_ready"
            )
            assert (
                fresh.execute(
                    "retrieve_context", '{"query":"newer"}', evidence_prefix="E1"
                ).observation.error_code
                == "index_not_ready"
            )
            result = run_investigation(
                AgentRequest(
                    repository_id=scope.repository_id,
                    snapshot_id=scope.snapshot_id,
                    question="Inspect run and its saved return value",
                ),
                registry=registry,
                provider=ScriptedProvider(
                    call("search_symbol", {"query": "run"}, "symbol"),
                    call("read_file", {"path": "app.py"}, "read"),
                    AgentTurn(text="run returns a saved literal [E2_1]."),
                ),
            )
            assert result.stop_reason == "completed" and result.total_steps == 2
            assert "100%_literal" in result.sources[-1].content
            assert "newer" not in result.model_dump_json()
            local = run_investigation(
                AgentRequest(
                    repository_id=scope.repository_id,
                    snapshot_id=scope.snapshot_id,
                    question="run literal",
                ),
                registry=registry,
                provider=DeterministicAgentProvider(),
            )
            assert local.stop_reason == "completed" and local.total_steps == 2
            # Exercise the bound using persisted content with heavily escaped lines.
            saved = session.scalar(
                select(SnapshotFile).where(
                    SnapshotFile.snapshot_id == scope.snapshot_id
                )
            )
            saved.content = '"\\' * 20_000
            session.flush()
            bounded = ToolRegistry(
                session,
                scope,
                embedding_factory=DeterministicEmbeddingProvider,
                observation_limit=1_000,
            )
            result = bounded.execute(
                "read_file", '{"path":"app.py"}', evidence_prefix="E1"
            )
            assert result.observation.truncated
            assert len(result.observation.model_dump_json()) <= 1_000
    finally:
        with factory() as session:
            session.execute(delete(Repository).where(Repository.id.in_(repository_ids)))
            session.commit()
        engine.dispose()
