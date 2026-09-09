from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.embeddings.providers import (
    EmbeddingConfigurationError,
    create_embedding_provider,
)
from repopilot.retrieval.retriever import (
    RetrievalSnapshotNotFoundError,
    SnapshotNotIndexedError,
    retrieve_evidence,
)


class RetrieveRequest(BaseModel):
    repository_id: int = Field(gt=0)
    snapshot_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=4_000)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def require_non_whitespace_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Question must not be empty")
        return normalized


class RetrievalEvidenceResponse(BaseModel):
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


class RetrieveResponse(BaseModel):
    repository_id: int
    snapshot_id: int
    question: str
    top_k: int
    embedding_provider: str
    embedding_model: str
    duration_ms: float
    evidence: list[RetrievalEvidenceResponse]


router = APIRouter(prefix="/api", tags=["retrieval"])


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_repository_evidence(
    payload: RetrieveRequest,
    request: Request,
    session: Annotated[Session, Depends(get_database_session)],
) -> RetrieveResponse:
    settings: Settings = request.app.state.settings
    try:
        provider = create_embedding_provider(settings)
        result = retrieve_evidence(
            session,
            repository_id=payload.repository_id,
            snapshot_id=payload.snapshot_id,
            question=payload.question,
            top_k=payload.top_k,
            provider=provider,
        )
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except RetrievalSnapshotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except SnapshotNotIndexedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return RetrieveResponse(
        repository_id=result.repository_id,
        snapshot_id=result.snapshot_id,
        question=result.question,
        top_k=result.top_k,
        embedding_provider=result.embedding_provider,
        embedding_model=result.embedding_model,
        duration_ms=result.duration_ms,
        evidence=[RetrievalEvidenceResponse(**item.__dict__) for item in result.evidence],
    )
