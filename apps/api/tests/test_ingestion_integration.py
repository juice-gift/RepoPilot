import os
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select

from repopilot.config import Settings
from repopilot.db.models import Repository, RepositorySnapshot, SnapshotFile
from repopilot.db.session import (
    create_database_engine,
    create_database_session_factory,
)
from repopilot.ingestion.service import ingest_repository

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="set RUN_DATABASE_TESTS=1 to run live PostgreSQL tests",
)


def test_repository_ingestion_persists_idempotent_content_snapshot(
    tmp_path: Path,
) -> None:
    repository_path = tmp_path / "sample"
    repository_path.mkdir()
    source = repository_path / "app.py"
    source.write_text("def answer():\n    return 42\n", encoding="utf-8")
    (repository_path / ".env").write_text("TOKEN=excluded\n", encoding="utf-8")

    settings = Settings()
    engine = create_database_engine(settings.database_url)
    session_factory = create_database_session_factory(engine)

    try:
        with session_factory() as session:
            first = ingest_repository(
                session,
                requested_path=str(repository_path),
                allowed_root=tmp_path,
            )
            repeated = ingest_repository(
                session,
                requested_path=str(repository_path),
                allowed_root=tmp_path,
            )

            assert first.snapshot_created is True
            assert repeated.snapshot_created is False
            assert repeated.snapshot.id == first.snapshot.id
            assert session.scalar(
                select(func.count()).select_from(SnapshotFile).where(
                    SnapshotFile.snapshot_id == first.snapshot.id
                )
            ) == 1

            source.write_text("def answer():\n    return 43\n", encoding="utf-8")
            changed = ingest_repository(
                session,
                requested_path=str(repository_path),
                allowed_root=tmp_path,
            )
            assert changed.snapshot_created is True
            assert changed.snapshot.id != first.snapshot.id
            assert changed.snapshot.content_hash != first.snapshot.content_hash

            session.execute(delete(Repository).where(Repository.id == first.repository.id))
            session.commit()
            assert session.scalar(
                select(func.count()).select_from(RepositorySnapshot).where(
                    RepositorySnapshot.repository_id == first.repository.id
                )
            ) == 0
    finally:
        engine.dispose()
