from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.embeddings.providers import (
    EmbeddingConfigurationError,
    create_embedding_provider,
)
from repopilot.rag.generation import (
    GenerationConfigurationError,
    create_generation_provider,
)
from repopilot.rag.service import GenerationFailedError, answer_repository_question
from repopilot.retrieval.retriever import (
    RetrievalSnapshotNotFoundError,
    SnapshotNotIndexedError,
)


class AskRequest(BaseModel):
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


class RagEvidenceResponse(BaseModel):
    evidence_id: str | None
    included_in_context: bool
    truncated: bool
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


class CitationResponse(BaseModel):
    evidence_id: str
    chunk_id: int
    file_path: str
    symbol_name: str | None
    qualified_name: str | None
    start_line: int
    end_line: int
    score: float
    content: str


class AskResponse(BaseModel):
    status: Literal["answered", "insufficient_evidence"]
    repository_id: int
    snapshot_id: int
    question: str
    answer: str
    embedding_provider: str
    embedding_model: str
    retrieval_strategy: Literal["vector", "hybrid"]
    generation_provider: str
    generation_model: str
    retrieval_duration_ms: float
    generation_duration_ms: float
    context_character_count: int
    context_character_limit: int
    omitted_evidence_count: int
    invalid_evidence_ids: list[str]
    citations: list[CitationResponse]
    evidence: list[RagEvidenceResponse]


router = APIRouter(prefix="/api", tags=["rag"])


@router.post("/ask", response_model=AskResponse)
def ask_repository_question(
    payload: AskRequest,
    request: Request,
    session: Annotated[Session, Depends(get_database_session)],
) -> AskResponse:
    settings: Settings = request.app.state.settings
    try:
        embedding_provider = create_embedding_provider(settings)
        generation_provider = create_generation_provider(settings)
        result = answer_repository_question(
            session,
            repository_id=payload.repository_id,
            snapshot_id=payload.snapshot_id,
            question=payload.question,
            top_k=payload.top_k,
            context_character_limit=settings.context_character_limit,
            context_max_evidence=settings.context_max_evidence,
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
            retrieval_strategy=settings.retrieval_strategy,
        )
    except (EmbeddingConfigurationError, GenerationConfigurationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except RetrievalSnapshotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except SnapshotNotIndexedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except GenerationFailedError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    context_by_chunk = {
        item.evidence.chunk_id: item for item in result.context.evidence
    }
    evidence = []
    for item in result.retrieval.evidence:
        context_item = context_by_chunk.get(item.chunk_id)
        evidence.append(
            RagEvidenceResponse(
                evidence_id=context_item.evidence_id if context_item else None,
                included_in_context=context_item is not None,
                truncated=context_item.truncated if context_item else False,
                **item.__dict__,
            )
        )
    return AskResponse(
        status=result.status,
        repository_id=result.retrieval.repository_id,
        snapshot_id=result.retrieval.snapshot_id,
        question=result.retrieval.question,
        answer=result.answer,
        embedding_provider=result.retrieval.embedding_provider,
        embedding_model=result.retrieval.embedding_model,
        retrieval_strategy=result.retrieval.retrieval_strategy,
        generation_provider=result.generation_provider,
        generation_model=result.generation_model,
        retrieval_duration_ms=result.retrieval.duration_ms,
        generation_duration_ms=result.generation_duration_ms,
        context_character_count=result.context.character_count,
        context_character_limit=settings.context_character_limit,
        omitted_evidence_count=result.context.omitted_evidence_count,
        invalid_evidence_ids=list(result.citations.invalid_evidence_ids),
        citations=[CitationResponse(**item.__dict__) for item in result.citations.citations],
        evidence=evidence,
    )
