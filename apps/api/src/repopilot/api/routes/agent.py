from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from repopilot.agent.models import AgentRequest, AgentResult
from repopilot.agent.runner import RunLimits, run_investigation
from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.embeddings.providers import create_embedding_provider
from repopilot.intelligence.service import SnapshotNotFoundError
from repopilot.rag.generation import GenerationConfigurationError, create_agent_provider

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/investigate", response_model=AgentResult)
def investigate(
    payload: AgentRequest,
    request: Request,
    session: Annotated[Session, Depends(get_database_session)],
) -> AgentResult:
    settings: Settings = request.app.state.settings
    try:
        registry = ToolRegistry(
            session,
            RunScope(payload.repository_id, payload.snapshot_id),
            embedding_factory=lambda: create_embedding_provider(settings),
            retrieval_strategy=settings.retrieval_strategy,
            observation_limit=settings.agent_observation_character_limit,
        )
        return run_investigation(
            payload,
            registry=registry,
            provider=create_agent_provider(settings),
            limits=RunLimits(
                max_steps=settings.agent_max_steps,
                context_characters=settings.agent_context_character_limit,
                model_output_characters=settings.agent_model_output_character_limit,
            ),
        )
    except GenerationConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SnapshotNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail="Repository database is unavailable"
        ) from exc
