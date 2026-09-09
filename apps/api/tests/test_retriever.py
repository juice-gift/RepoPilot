from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.indexing.vector_store import VectorSearchRow
from repopilot.retrieval.retriever import (
    SnapshotNotIndexedError,
    retrieve_evidence,
)


def test_retriever_returns_ranked_source_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = DeterministicEmbeddingProvider()
    snapshot = SimpleNamespace(
        indexed_at=object(),
        embedding_provider=provider.provider_name,
        embedding_model=provider.model_name,
        embedding_dimensions=provider.dimensions,
        indexed_chunk_count=1,
        chunk_count=1,
    )
    chunk = SimpleNamespace(
        id=7,
        language="python",
        chunk_type="function",
        symbol_name="answer",
        qualified_name="answer",
        parent_symbol=None,
        start_line=10,
        end_line=12,
        content_hash="a" * 64,
        raw_content="def answer():\n    return 42\n",
    )
    session = MagicMock(spec=Session)
    session.scalar.return_value = snapshot
    monkeypatch.setattr(
        "repopilot.retrieval.retriever.exact_vector_search",
        lambda *args, **kwargs: [VectorSearchRow(chunk, "app.py", 0.125)],
    )

    result = retrieve_evidence(
        session,
        repository_id=1,
        snapshot_id=2,
        question="  where is the answer?  ",
        top_k=3,
        provider=provider,
        strategy="vector",
    )

    assert result.question == "where is the answer?"
    assert result.evidence[0].rank == 1
    assert result.evidence[0].chunk_id == 7
    assert result.evidence[0].file_path == "app.py"
    assert result.evidence[0].score == 0.875
    assert result.evidence[0].distance == 0.125


def test_retriever_rejects_provider_mismatch() -> None:
    provider = DeterministicEmbeddingProvider()
    snapshot = SimpleNamespace(
        indexed_at=object(),
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=512,
        indexed_chunk_count=1,
        chunk_count=1,
    )
    session = MagicMock(spec=Session)
    session.scalar.return_value = snapshot

    with pytest.raises(SnapshotNotIndexedError, match="configured"):
        retrieve_evidence(
            session,
            repository_id=1,
            snapshot_id=2,
            question="question",
            top_k=5,
            provider=provider,
        )
