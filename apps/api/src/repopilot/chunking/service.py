from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from repopilot.chunking.chunker import CHUNKING_VERSION, chunk_source
from repopilot.db.models import CodeChunk, RepositorySnapshot, SnapshotFile


class SnapshotNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class ChunkingResult:
    snapshot: RepositorySnapshot
    chunks: tuple[CodeChunk, ...]
    chunks_created: bool


def chunk_snapshot(
    session: Session, *, repository_id: int, snapshot_id: int
) -> ChunkingResult:
    snapshot = session.scalar(
        select(RepositorySnapshot).where(
            RepositorySnapshot.id == snapshot_id,
            RepositorySnapshot.repository_id == repository_id,
        )
    )
    if snapshot is None:
        raise SnapshotNotFoundError("Repository snapshot not found")

    if snapshot.chunking_version == CHUNKING_VERSION:
        existing = tuple(
            session.scalars(
                select(CodeChunk)
                .where(CodeChunk.snapshot_id == snapshot_id)
                .order_by(CodeChunk.snapshot_file_id, CodeChunk.sequence)
            ).all()
        )
        if len(existing) == snapshot.chunk_count:
            return ChunkingResult(snapshot, existing, False)

    session.execute(delete(CodeChunk).where(CodeChunk.snapshot_id == snapshot_id))
    files = session.scalars(
        select(SnapshotFile)
        .where(SnapshotFile.snapshot_id == snapshot_id)
        .order_by(SnapshotFile.path)
    ).all()
    chunks: list[CodeChunk] = []
    for file in files:
        for draft in chunk_source(file.path, file.language, file.content):
            chunk = CodeChunk(
                snapshot_id=snapshot.id,
                snapshot_file_id=file.id,
                sequence=draft.sequence,
                language=draft.language,
                chunk_type=draft.chunk_type,
                symbol_name=draft.symbol_name,
                qualified_name=draft.qualified_name,
                parent_symbol=draft.parent_symbol,
                start_line=draft.start_line,
                end_line=draft.end_line,
                content_hash=draft.content_hash,
                chunking_version=draft.chunking_version,
                raw_content=draft.raw_content,
                embedding_content=draft.embedding_content,
            )
            session.add(chunk)
            chunks.append(chunk)

    snapshot.chunk_count = len(chunks)
    snapshot.chunking_version = CHUNKING_VERSION
    session.commit()
    for chunk in chunks:
        session.refresh(chunk)
    session.refresh(snapshot)
    return ChunkingResult(snapshot, tuple(chunks), True)
