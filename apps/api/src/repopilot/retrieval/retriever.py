from dataclasses import dataclass
from time import perf_counter
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from repopilot.db.models import RepositorySnapshot
from repopilot.embeddings.providers import EmbeddingProvider
from repopilot.indexing.vector_store import exact_vector_search
from repopilot.retrieval.lexical import rerank_hybrid

RetrievalStrategy = Literal["vector", "hybrid"]


class RetrievalSnapshotNotFoundError(ValueError):
    pass


class SnapshotNotIndexedError(ValueError):
    pass


@dataclass(frozen=True)
class RetrievalEvidence:
    rank: int
    chunk_id: int
    file_path: str
    language: str
    chunk_type: str
    symbol_name: str | None
    qualified_name: str | None
    parent_symbol: str | None
    start_line: int
    end_line: int
    content_hash: str
    score: float
    distance: float
    content: str


@dataclass(frozen=True)
class RetrievalResult:
    repository_id: int
    snapshot_id: int
    question: str
    top_k: int
    embedding_provider: str
    embedding_model: str
    retrieval_strategy: RetrievalStrategy
    duration_ms: float
    evidence: tuple[RetrievalEvidence, ...]


def retrieve_evidence(
    session: Session,
    *,
    repository_id: int,
    snapshot_id: int,
    question: str,
    top_k: int,
    provider: EmbeddingProvider,
    strategy: RetrievalStrategy = "hybrid",
) -> RetrievalResult:
    started = perf_counter()
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("Question must not be empty")
    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")
    if strategy not in ("vector", "hybrid"):
        raise ValueError("strategy must be vector or hybrid")

    snapshot = session.scalar(
        select(RepositorySnapshot).where(
            RepositorySnapshot.id == snapshot_id,
            RepositorySnapshot.repository_id == repository_id,
        )
    )
    if snapshot is None:
        raise RetrievalSnapshotNotFoundError("Repository snapshot not found")
    if (
        snapshot.indexed_at is None
        or snapshot.embedding_provider != provider.provider_name
        or snapshot.embedding_model != provider.model_name
        or snapshot.embedding_dimensions != provider.dimensions
        or snapshot.indexed_chunk_count != snapshot.chunk_count
    ):
        raise SnapshotNotIndexedError(
            "Snapshot is not indexed with the configured embedding provider"
        )

    query_embedding = provider.embed([normalized_question])[0]
    vector_limit = top_k if strategy == "vector" else snapshot.chunk_count
    rows = exact_vector_search(
        session,
        snapshot_id=snapshot_id,
        query_embedding=query_embedding,
        limit=vector_limit,
    )
    ranked_rows = (
        [(row, 1.0 - row.distance) for row in rows]
        if strategy == "vector"
        else [
            (item.vector_row, item.score)
            for item in rerank_hybrid(rows, question=normalized_question, limit=top_k)
        ]
    )
    evidence = tuple(
        RetrievalEvidence(
            rank=rank,
            chunk_id=row.chunk.id,
            file_path=row.file_path,
            language=row.chunk.language,
            chunk_type=row.chunk.chunk_type,
            symbol_name=row.chunk.symbol_name,
            qualified_name=row.chunk.qualified_name,
            parent_symbol=row.chunk.parent_symbol,
            start_line=row.chunk.start_line,
            end_line=row.chunk.end_line,
            content_hash=row.chunk.content_hash,
            score=round(score, 6),
            distance=round(row.distance, 6),
            content=row.chunk.raw_content,
        )
        for rank, (row, score) in enumerate(ranked_rows, start=1)
    )
    return RetrievalResult(
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        question=normalized_question,
        top_k=top_k,
        embedding_provider=provider.provider_name,
        embedding_model=provider.model_name,
        retrieval_strategy=strategy,
        duration_ms=round((perf_counter() - started) * 1000, 3),
        evidence=evidence,
    )
