from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.chunking.service import SnapshotNotFoundError
from repopilot.config import Settings
from repopilot.embeddings.providers import (
    EmbeddingConfigurationError,
    create_embedding_provider,
)
from repopilot.indexing.service import index_snapshot


class IndexSnapshotResponse(BaseModel):
    repository_id: int
    snapshot_id: int
    chunk_count: int
    embedded_chunk_count: int
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    index_reused: bool
    duration_ms: float


router = APIRouter(prefix="/api/repositories", tags=["indexing"])


@router.post(
    "/{repository_id}/snapshots/{snapshot_id}/index",
    response_model=IndexSnapshotResponse,
)
def create_snapshot_index(
    repository_id: int,
    snapshot_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_database_session)],
) -> IndexSnapshotResponse:
    settings: Settings = request.app.state.settings
    try:
        provider = create_embedding_provider(settings)
        result = index_snapshot(
            session,
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            provider=provider,
        )
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except SnapshotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return IndexSnapshotResponse(**result.__dict__)
