from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.chunking.service import SnapshotNotFoundError, chunk_snapshot
from repopilot.db.models import CodeChunk, RepositorySnapshot, SnapshotFile


class ChunkResponse(BaseModel):
    id: int
    snapshot_id: int
    file_path: str
    sequence: int
    language: str
    chunk_type: str
    symbol_name: str | None
    qualified_name: str | None
    parent_symbol: str | None
    start_line: int
    end_line: int
    content_hash: str
    chunking_version: str
    raw_content: str
    embedding_content: str


class ChunkSnapshotResponse(BaseModel):
    repository_id: int
    snapshot_id: int
    chunk_count: int
    chunking_version: str
    chunks_created: bool
    chunks: list[ChunkResponse]


router = APIRouter(prefix="/api/repositories", tags=["chunks"])


def _chunk_response(chunk: CodeChunk, file_path: str) -> ChunkResponse:
    return ChunkResponse(
        id=chunk.id,
        snapshot_id=chunk.snapshot_id,
        file_path=file_path,
        sequence=chunk.sequence,
        language=chunk.language,
        chunk_type=chunk.chunk_type,
        symbol_name=chunk.symbol_name,
        qualified_name=chunk.qualified_name,
        parent_symbol=chunk.parent_symbol,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        content_hash=chunk.content_hash,
        chunking_version=chunk.chunking_version,
        raw_content=chunk.raw_content,
        embedding_content=chunk.embedding_content,
    )


@router.post(
    "/{repository_id}/snapshots/{snapshot_id}/chunks",
    response_model=ChunkSnapshotResponse,
)
def create_snapshot_chunks(
    repository_id: int,
    snapshot_id: int,
    session: Annotated[Session, Depends(get_database_session)],
) -> ChunkSnapshotResponse:
    try:
        result = chunk_snapshot(
            session, repository_id=repository_id, snapshot_id=snapshot_id
        )
    except SnapshotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    file_paths = {
        file.id: file.path
        for file in session.scalars(
            select(SnapshotFile).where(SnapshotFile.snapshot_id == snapshot_id)
        ).all()
    }
    return ChunkSnapshotResponse(
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        chunk_count=len(result.chunks),
        chunking_version=result.snapshot.chunking_version or "",
        chunks_created=result.chunks_created,
        chunks=[
            _chunk_response(chunk, file_paths[chunk.snapshot_file_id])
            for chunk in result.chunks
        ],
    )


@router.get(
    "/{repository_id}/snapshots/{snapshot_id}/chunks",
    response_model=list[ChunkResponse],
)
def list_snapshot_chunks(
    repository_id: int,
    snapshot_id: int,
    session: Annotated[Session, Depends(get_database_session)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ChunkResponse]:
    snapshot = session.scalar(
        select(RepositorySnapshot).where(
            RepositorySnapshot.id == snapshot_id,
            RepositorySnapshot.repository_id == repository_id,
        )
    )
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository snapshot not found",
        )
    rows = session.execute(
        select(CodeChunk, SnapshotFile.path)
        .join(SnapshotFile, SnapshotFile.id == CodeChunk.snapshot_file_id)
        .where(CodeChunk.snapshot_id == snapshot_id)
        .order_by(SnapshotFile.path, CodeChunk.sequence)
        .limit(limit)
    ).all()
    return [_chunk_response(chunk, file_path) for chunk, file_path in rows]
