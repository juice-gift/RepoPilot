import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
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
from repopilot.main import create_app
from repopilot.rag.generation import DeterministicGenerationProvider
from repopilot.rag.service import answer_repository_question

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="set RUN_DATABASE_TESTS=1 to run live PostgreSQL tests",
)


def test_repository_to_grounded_answer_and_real_citation(tmp_path: Path) -> None:
    repository_path = tmp_path / "rag-sample"
    repository_path.mkdir()
    (repository_path / "orders.py").write_text(
        "def calculate_order_total(prices):\n    return sum(prices)\n",
        encoding="utf-8",
    )
    settings = Settings()
    engine = create_database_engine(settings.database_url)
    session_factory = create_database_session_factory(engine)
    embedding_provider = DeterministicEmbeddingProvider()

    try:
        with session_factory() as session:
            ingestion = ingest_repository(
                session, requested_path=str(repository_path), allowed_root=tmp_path
            )
            index_snapshot(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
                provider=embedding_provider,
            )
            result = answer_repository_question(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
                question="Where is the order total calculated?",
                top_k=3,
                context_character_limit=4_000,
                context_max_evidence=3,
                embedding_provider=embedding_provider,
                generation_provider=DeterministicGenerationProvider(),
            )

            assert result.status == "answered"
            assert "[E1]" in result.answer
            assert result.citations.citations
            citation = result.citations.citations[0]
            assert citation.file_path == "orders.py"
            assert citation.qualified_name == "calculate_order_total"
            assert citation.start_line == 1
            assert citation.end_line == 2
            assert citation.content.startswith("def calculate_order_total")

            app_settings = Settings(
                database_url=settings.database_url,
                repository_allowed_root=tmp_path,
                embedding_provider="deterministic",
                generation_provider="deterministic",
                _env_file=None,
            )
            app = create_app(settings=app_settings, database_engine=engine)
            with TestClient(app) as client:
                response = client.post(
                    "/api/ask",
                    json={
                        "repository_id": ingestion.repository.id,
                        "snapshot_id": ingestion.snapshot.id,
                        "question": "Where is the order total calculated?",
                        "top_k": 3,
                    },
                )
                assert response.status_code == 200
                payload = response.json()
                assert payload["status"] == "answered"
                assert payload["citations"][0]["file_path"] == "orders.py"
                assert payload["evidence"][0]["evidence_id"] == "E1"

            session.execute(
                delete(Repository).where(Repository.id == ingestion.repository.id)
            )
            session.commit()
    finally:
        engine.dispose()
