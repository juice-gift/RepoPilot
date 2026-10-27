from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.embeddings.providers import create_embedding_provider
from repopilot.intelligence.service import SnapshotNotFoundError
from repopilot.rag.generation import GenerationConfigurationError, create_agent_provider
from repopilot.resolution.models import ResolutionRequest, ResolutionResult
from repopilot.resolution.sandbox import SandboxError, SandboxExecutor
from repopilot.resolution.service import resolve_snapshot
from repopilot.resolution.tools import ResolutionLimits
from repopilot.resolution.workspace import WorkspaceError

router = APIRouter(prefix="/api/agent", tags=["resolution"])


@router.post("/resolve", response_model=ResolutionResult)
def resolve(
    payload: ResolutionRequest,
    request: Request,
    session: Annotated[Session, Depends(get_database_session)],
) -> ResolutionResult:
    settings: Settings = request.app.state.settings
    if not settings.resolution_sandbox_image:
        raise HTTPException(
            status_code=503,
            detail="Prepare the controlled Docker test image and configure RESOLUTION_SANDBOX_IMAGE",
        )
    try:
        baseline = ToolRegistry(
            session,
            RunScope(payload.repository_id, payload.snapshot_id),
            embedding_factory=lambda: create_embedding_provider(settings),
            retrieval_strategy=settings.retrieval_strategy,
            observation_limit=settings.agent_observation_character_limit,
        )
        return resolve_snapshot(
            payload,
            session=session,
            baseline=baseline,
            provider=create_agent_provider(settings),
            executor=SandboxExecutor(settings.resolution_sandbox_image),
            limits=ResolutionLimits(
                context_characters=settings.agent_context_character_limit,
                model_output_characters=settings.agent_model_output_character_limit,
                observation_characters=settings.agent_observation_character_limit,
            ),
        )
    except SnapshotNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail="Repository snapshot not found"
        ) from exc
    except WorkspaceError as exc:
        raise HTTPException(
            status_code=409,
            detail="Snapshot is not eligible for this approved resolution profile, or saved source failed validation",
        ) from exc
    except (SandboxError, GenerationConfigurationError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Resolution sandbox or model provider is not configured",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail="Repository database is unavailable"
        ) from exc
