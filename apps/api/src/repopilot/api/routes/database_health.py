from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.db.health import check_database_connection


class DatabaseHealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["postgresql"]


router = APIRouter(prefix="/api")


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unavailable"}},
)
def get_database_health(
    session: Annotated[Session, Depends(get_database_session)],
) -> DatabaseHealthResponse:
    try:
        check_database_connection(session)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return DatabaseHealthResponse(status="ok", database="postgresql")
