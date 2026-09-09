from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.main import create_app
from repopilot.retrieval.retriever import RetrievalEvidence, RetrievalResult


def test_retrieval_api_exposes_evidence_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    provider = DeterministicEmbeddingProvider()
    result = RetrievalResult(
        repository_id=1,
        snapshot_id=2,
        question="Where is the answer?",
        top_k=5,
        embedding_provider=provider.provider_name,
        embedding_model=provider.model_name,
        duration_ms=1.25,
        evidence=(
            RetrievalEvidence(
                rank=1,
                chunk_id=7,
                file_path="app.py",
                language="python",
                chunk_type="function",
                symbol_name="answer",
                qualified_name="answer",
                parent_symbol=None,
                start_line=1,
                end_line=2,
                content_hash="a" * 64,
                score=0.9,
                distance=0.1,
                content="def answer():\n    return 42\n",
            ),
        ),
    )
    monkeypatch.setattr(
        "repopilot.api.routes.retrieval.create_embedding_provider",
        lambda settings: provider,
    )
    monkeypatch.setattr(
        "repopilot.api.routes.retrieval.retrieve_evidence",
        lambda *args, **kwargs: result,
    )
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/database",
        repository_allowed_root=tmp_path,
        embedding_provider="deterministic",
        _env_file=None,
    )
    app = create_app(settings=settings)
    session = MagicMock(spec=Session)

    def override_database_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_database_session] = override_database_session
    with TestClient(app) as client:
        response = client.post(
            "/api/retrieve",
            json={
                "repository_id": 1,
                "snapshot_id": 2,
                "question": "Where is the answer?",
            },
        )

    assert response.status_code == 200
    assert response.json()["evidence"][0]["file_path"] == "app.py"
    assert response.json()["evidence"][0]["start_line"] == 1
    assert response.json()["evidence"][0]["score"] == 0.9


def test_retrieval_api_rejects_whitespace_question(tmp_path: Path) -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/database",
        repository_allowed_root=tmp_path,
        embedding_provider="deterministic",
        _env_file=None,
    )
    app = create_app(settings=settings)
    session = MagicMock(spec=Session)

    def override_database_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_database_session] = override_database_session
    with TestClient(app) as client:
        response = client.post(
            "/api/retrieve",
            json={"repository_id": 1, "snapshot_id": 2, "question": "   "},
        )

    assert response.status_code == 422
