from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from repopilot.db.models import CodeChunk, SnapshotFile


@dataclass(frozen=True)
class VectorSearchRow:
    chunk: CodeChunk
    file_path: str
    distance: float


def exact_vector_search(
    session: Session,
    *,
    snapshot_id: int,
    query_embedding: list[float],
    limit: int,
) -> list[VectorSearchRow]:
    distance = CodeChunk.embedding.cosine_distance(query_embedding).label("distance")
    rows = session.execute(
        select(CodeChunk, SnapshotFile.path, distance)
        .join(SnapshotFile, SnapshotFile.id == CodeChunk.snapshot_file_id)
        .where(
            CodeChunk.snapshot_id == snapshot_id,
            CodeChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(limit)
    ).all()
    return [
        VectorSearchRow(chunk=chunk, file_path=file_path, distance=float(value))
        for chunk, file_path, value in rows
    ]
