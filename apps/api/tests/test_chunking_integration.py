import os
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select

from repopilot.chunking.chunker import CHUNKING_VERSION
from repopilot.chunking.service import chunk_snapshot
from repopilot.config import Settings
from repopilot.db.models import CodeChunk, Repository
from repopilot.db.session import (
    create_database_engine,
    create_database_session_factory,
)
from repopilot.ingestion.service import ingest_repository

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="set RUN_DATABASE_TESTS=1 to run live PostgreSQL tests",
)


def test_snapshot_chunking_persists_metadata_and_is_idempotent(tmp_path: Path) -> None:
    repository_path = tmp_path / "chunk-sample"
    repository_path.mkdir()
    (repository_path / "service.py").write_text(
        "class Service:\n    def run(self):\n        return 'ok'\n",
        encoding="utf-8",
    )
    settings = Settings()
    engine = create_database_engine(settings.database_url)
    session_factory = create_database_session_factory(engine)

    try:
        with session_factory() as session:
            ingestion = ingest_repository(
                session,
                requested_path=str(repository_path),
                allowed_root=tmp_path,
            )
            first = chunk_snapshot(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
            )
            repeated = chunk_snapshot(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
            )

            assert first.chunks_created is True
            assert repeated.chunks_created is False
            assert [chunk.id for chunk in repeated.chunks] == [
                chunk.id for chunk in first.chunks
            ]
            assert first.snapshot.chunking_version == CHUNKING_VERSION
            assert any(
                chunk.qualified_name == "Service.run" and chunk.parent_symbol == "Service"
                for chunk in first.chunks
            )
            assert session.scalar(
                select(func.count()).select_from(CodeChunk).where(
                    CodeChunk.snapshot_id == ingestion.snapshot.id
                )
            ) == first.snapshot.chunk_count

            session.execute(
                delete(Repository).where(Repository.id == ingestion.repository.id)
            )
            session.commit()
    finally:
        engine.dispose()
