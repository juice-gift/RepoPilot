from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.db.models import Repository, RepositorySnapshot
from repopilot.ingestion.scanner import NoSupportedFilesError, RepositoryPathError
from repopilot.ingestion.service import ingest_repository


class RepositoryIngestRequest(BaseModel):
    path: str = Field(min_length=1, max_length=4096)
    name: str | None = Field(default=None, min_length=1, max_length=255)


class SkippedFileResponse(BaseModel):
    path: str
    reason: str


class RepositoryResponse(BaseModel):
    id: int
    name: str
    local_path: str
    created_at: datetime


class SnapshotResponse(BaseModel):
    id: int
    repository_id: int
    content_hash: str
    source_revision: str | None
    accepted_file_count: int
    skipped_file_count: int
    total_bytes: int
    created_at: datetime


class RepositoryIngestResponse(BaseModel):
    repository: RepositoryResponse
    snapshot: SnapshotResponse
    snapshot_created: bool
    languages: dict[str, int]
    skipped_reason_counts: dict[str, int]
    skipped_files: list[SkippedFileResponse]
    excluded_directories: list[str]


router = APIRouter(prefix="/api/repositories", tags=["repositories"])


def _repository_response(repository: Repository) -> RepositoryResponse:
    return RepositoryResponse(
        id=repository.id,
        name=repository.name,
        local_path=repository.local_path,
        created_at=repository.created_at,
    )


def _snapshot_response(snapshot: RepositorySnapshot) -> SnapshotResponse:
    return SnapshotResponse(
        id=snapshot.id,
        repository_id=snapshot.repository_id,
        content_hash=snapshot.content_hash,
        source_revision=snapshot.source_revision,
        accepted_file_count=snapshot.accepted_file_count,
        skipped_file_count=snapshot.skipped_file_count,
        total_bytes=snapshot.total_bytes,
        created_at=snapshot.created_at,
    )


@router.post(
    "/ingest",
    response_model=RepositoryIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_local_repository(
    payload: RepositoryIngestRequest,
    request: Request,
    session: Annotated[Session, Depends(get_database_session)],
) -> RepositoryIngestResponse:
    settings: Settings = request.app.state.settings
    try:
        result = ingest_repository(
            session,
            requested_path=payload.path,
            allowed_root=settings.repository_allowed_root,
            repository_name=payload.name,
        )
    except (RepositoryPathError, NoSupportedFilesError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    language_counts: dict[str, int] = {}
    for file in result.scan.files:
        language_counts[file.language] = language_counts.get(file.language, 0) + 1

    return RepositoryIngestResponse(
        repository=_repository_response(result.repository),
        snapshot=_snapshot_response(result.snapshot),
        snapshot_created=result.snapshot_created,
        languages=language_counts,
        skipped_reason_counts=result.scan.skipped_reason_counts,
        skipped_files=[
            SkippedFileResponse(path=item.path, reason=item.reason)
            for item in result.scan.skipped_files[:50]
        ],
        excluded_directories=list(result.scan.excluded_directories),
    )


@router.get("", response_model=list[RepositoryResponse])
def list_repositories(
    session: Annotated[Session, Depends(get_database_session)],
) -> list[RepositoryResponse]:
    repositories = session.scalars(select(Repository).order_by(Repository.name)).all()
    return [_repository_response(repository) for repository in repositories]


@router.get("/{repository_id}/snapshots", response_model=list[SnapshotResponse])
def list_repository_snapshots(
    repository_id: int,
    session: Annotated[Session, Depends(get_database_session)],
) -> list[SnapshotResponse]:
    repository = session.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    snapshots = session.scalars(
        select(RepositorySnapshot)
        .where(RepositorySnapshot.repository_id == repository_id)
        .order_by(RepositorySnapshot.created_at.desc())
    ).all()
    return [_snapshot_response(snapshot) for snapshot in snapshots]
