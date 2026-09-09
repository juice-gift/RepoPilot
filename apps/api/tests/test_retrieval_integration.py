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
from repopilot.ingestion.service import ingest_repository
from repopilot.retrieval.retriever import retrieve_evidence

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="set RUN_DATABASE_TESTS=1 to run live PostgreSQL tests",
)


def test_retrieval_is_isolated_to_requested_repository_snapshot(tmp_path: Path) -> None:
    first_path = tmp_path / "first-repository"
    first_path.mkdir()
    (first_path / "payments.py").write_text(
        "def capture_payment(order):\n    return order.total\n", encoding="utf-8"
    )
    second_path = tmp_path / "second-repository"
    second_path.mkdir()
    (second_path / "admin.py").write_text(
        "def capture_payment(order):\n    raise RuntimeError('not available')\n",
        encoding="utf-8",
    )
    settings = Settings()
    engine = create_database_engine(settings.database_url)
    session_factory = create_database_session_factory(engine)
    provider = DeterministicEmbeddingProvider()

    try:
        with session_factory() as session:
            first = ingest_repository(
                session, requested_path=str(first_path), allowed_root=tmp_path
            )
            second = ingest_repository(
                session, requested_path=str(second_path), allowed_root=tmp_path
            )
            for ingestion in (first, second):
                index_snapshot(
                    session,
                    repository_id=ingestion.repository.id,
                    snapshot_id=ingestion.snapshot.id,
                    provider=provider,
                )

            result = retrieve_evidence(
                session,
                repository_id=first.repository.id,
                snapshot_id=first.snapshot.id,
                question="capture payment order total",
                top_k=10,
                provider=provider,
            )

            assert result.evidence
            assert {item.file_path for item in result.evidence} == {"payments.py"}
            assert all("RuntimeError" not in item.content for item in result.evidence)

            session.execute(
                delete(Repository).where(
                    Repository.id.in_([first.repository.id, second.repository.id])
                )
            )
            session.commit()
    finally:
        engine.dispose()
