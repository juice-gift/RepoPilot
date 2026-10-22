import os
from pathlib import Path

import pytest
from sqlalchemy import delete, select

from repopilot.agent.tools import RunScope
from repopilot.config import Settings
from repopilot.db.models import Repository, SnapshotFile
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.ingestion.service import ingest_repository
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
                workspace.publish({"app.py": "value = 2\n"}, 0)
                assert workspace.read("app.py") == "value = 2\n"
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
