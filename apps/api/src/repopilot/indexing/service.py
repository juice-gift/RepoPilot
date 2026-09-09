from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from repopilot.chunking.service import SnapshotNotFoundError, chunk_snapshot
from repopilot.db.models import CodeChunk
from repopilot.embeddings.providers import EmbeddingProvider

EMBEDDING_BATCH_SIZE = 64


@dataclass(frozen=True)
class IndexingResult:
    repository_id: int
    snapshot_id: int
    chunk_count: int
    embedded_chunk_count: int
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    index_reused: bool
    duration_ms: float


def index_snapshot(
    session: Session,
    *,
    repository_id: int,
    snapshot_id: int,
    provider: EmbeddingProvider,
) -> IndexingResult:
    started = perf_counter()
    chunking = chunk_snapshot(
        session, repository_id=repository_id, snapshot_id=snapshot_id
    )
    snapshot = chunking.snapshot
    chunks = list(
        session.scalars(
            select(CodeChunk)
            .where(CodeChunk.snapshot_id == snapshot_id)
            .order_by(CodeChunk.id)
        ).all()
    )
    reusable = (
        snapshot.embedding_provider == provider.provider_name
        and snapshot.embedding_model == provider.model_name
        and snapshot.embedding_dimensions == provider.dimensions
        and snapshot.indexed_chunk_count == len(chunks)
        and all(chunk.embedding is not None for chunk in chunks)
    )
    if reusable:
        return _result(
            repository_id,
            snapshot_id,
            chunks,
            provider,
            index_reused=True,
            started=started,
        )

    embedded_at = datetime.now(UTC)
    for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        batch = chunks[start : start + EMBEDDING_BATCH_SIZE]
        vectors = provider.embed([chunk.embedding_content for chunk in batch])
        for chunk, vector in zip(batch, vectors, strict=True):
            chunk.embedding = vector
            chunk.embedding_provider = provider.provider_name
            chunk.embedding_model = provider.model_name
            chunk.embedded_at = embedded_at

    snapshot.embedding_provider = provider.provider_name
    snapshot.embedding_model = provider.model_name
    snapshot.embedding_dimensions = provider.dimensions
    snapshot.indexed_chunk_count = len(chunks)
    snapshot.indexed_at = embedded_at
    session.commit()
    return _result(
        repository_id,
        snapshot_id,
        chunks,
        provider,
        index_reused=False,
        started=started,
    )


def _result(
    repository_id: int,
    snapshot_id: int,
    chunks: list[CodeChunk],
    provider: EmbeddingProvider,
    *,
    index_reused: bool,
    started: float,
) -> IndexingResult:
    return IndexingResult(
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        chunk_count=len(chunks),
        embedded_chunk_count=len(chunks),
        embedding_provider=provider.provider_name,
        embedding_model=provider.model_name,
        embedding_dimensions=provider.dimensions,
        index_reused=index_reused,
        duration_ms=round((perf_counter() - started) * 1000, 3),
    )


__all__ = ["IndexingResult", "SnapshotNotFoundError", "index_snapshot"]
