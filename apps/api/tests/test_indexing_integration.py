import os
from pathlib import Path

import pytest
from sqlalchemy import delete

from repopilot.config import Settings
from repopilot.db.models import Repository
from repopilot.db.session import (
    create_database_engine,
    create_database_session_factory,
)
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.indexing.service import index_snapshot
from repopilot.indexing.vector_store import exact_vector_search
from repopilot.ingestion.service import ingest_repository

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="set RUN_DATABASE_TESTS=1 to run live PostgreSQL tests",
)


def test_snapshot_indexing_stores_vectors_and_exact_searches(tmp_path: Path) -> None:
    repository_path = tmp_path / "index-sample"
    repository_path.mkdir()
    (repository_path / "billing.py").write_text(
        "def calculate_invoice_total(items):\n    return sum(items)\n",
        encoding="utf-8",
    )
    (repository_path / "auth.py").write_text(
        "def verify_password(password):\n    return password == 'safe'\n",
        encoding="utf-8",
    )
    settings = Settings()
    engine = create_database_engine(settings.database_url)
    session_factory = create_database_session_factory(engine)
    provider = DeterministicEmbeddingProvider()

    try:
        with session_factory() as session:
            ingestion = ingest_repository(
                session,
                requested_path=str(repository_path),
                allowed_root=tmp_path,
            )
            first = index_snapshot(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
                provider=provider,
            )
            repeated = index_snapshot(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
                provider=provider,
            )
            query_vector = provider.embed(["calculate invoice total"])[0]
            results = exact_vector_search(
                session,
                snapshot_id=ingestion.snapshot.id,
                query_embedding=query_vector,
                limit=2,
            )

            assert first.index_reused is False
            assert repeated.index_reused is True
            assert first.embedded_chunk_count == first.chunk_count
            assert first.embedding_dimensions == 512
            assert results
            assert results[0].file_path == "billing.py"
            assert results[0].distance <= results[-1].distance

            session.execute(
                delete(Repository).where(Repository.id == ingestion.repository.id)
            )
            session.commit()
    finally:
        engine.dispose()
