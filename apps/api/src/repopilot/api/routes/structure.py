from collections.abc import Iterator
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.intelligence import navigation
from repopilot.intelligence.analysis import AnalysisError, ResolutionStatus
from repopilot.intelligence.service import SnapshotNotFoundError, index_structure


def _translate_errors(
    session: Annotated[Session, Depends(get_database_session)],
) -> Iterator[Session]:
    try:
        yield session
    except (SnapshotNotFoundError, navigation.ResourceNotFoundError) as exc:
        raise HTTPException(404, str(exc)) from exc
    except navigation.IndexNotReadyError as exc:
        raise HTTPException(409, str(exc)) from exc
    except AnalysisError as exc:
        raise HTTPException(422, str(exc)) from exc


Database = Annotated[Session, Depends(_translate_errors)]
PositiveId = Annotated[int, Path(gt=0)]
Limit = Annotated[int, Query(ge=1, le=500)]
Offset = Annotated[int, Query(ge=0)]
FilePath = Annotated[str, Query(min_length=1, max_length=4096)]

router = APIRouter(
    prefix="/api/repositories/{repository_id}/snapshots/{snapshot_id}/structure",
    tags=["code intelligence"],
)


class IndexResponse(BaseModel):
    snapshot_id: int
    index_version: str
    symbol_count: int
    import_count: int
    reference_count: int
    created: bool


@router.post("/index", response_model=IndexResponse)
def create_index(
    repository_id: PositiveId, snapshot_id: PositiveId, session: Database
) -> IndexResponse:
    return IndexResponse(
        **asdict(
            index_structure(
                session, repository_id=repository_id, snapshot_id=snapshot_id
            )
        )
    )


@router.get("/files", response_model=list[navigation.FileView])
def files(
    repository_id: PositiveId,
    snapshot_id: PositiveId,
    session: Database,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[navigation.FileView]:
    return navigation.list_files(
        session, repository_id, snapshot_id, limit=limit, offset=offset
    )


@router.get("/symbols", response_model=list[navigation.SymbolView])
def symbols(
    repository_id: PositiveId,
    snapshot_id: PositiveId,
    session: Database,
    q: Annotated[
        str | None, Query(min_length=1, max_length=255, pattern=r".*\S.*")
    ] = None,
    match: navigation.SymbolMatch = "exact",
    file_path: FilePath | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[navigation.SymbolView]:
    return navigation.search_symbols(
        session,
        repository_id,
        snapshot_id,
        query=q,
        match=match,
        file_path=file_path,
        limit=limit,
        offset=offset,
    )


@router.get("/symbols/{symbol_id}", response_model=navigation.DefinitionView)
def definition(
    repository_id: PositiveId,
    snapshot_id: PositiveId,
    symbol_id: PositiveId,
    session: Database,
) -> navigation.DefinitionView:
    return navigation.get_definition(session, repository_id, snapshot_id, symbol_id)


@router.get(
    "/symbols/{symbol_id}/references", response_model=list[navigation.ReferenceView]
)
def symbol_references(
    repository_id: PositiveId,
    snapshot_id: PositiveId,
    symbol_id: PositiveId,
    session: Database,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[navigation.ReferenceView]:
    return navigation.find_references(
        session,
        repository_id,
        snapshot_id,
        symbol_id=symbol_id,
        limit=limit,
        offset=offset,
    )


@router.get("/references", response_model=list[navigation.ReferenceView])
def references(
    repository_id: PositiveId,
    snapshot_id: PositiveId,
    session: Database,
    file_path: FilePath | None = None,
    status: ResolutionStatus | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[navigation.ReferenceView]:
    return navigation.find_references(
        session,
        repository_id,
        snapshot_id,
        file_path=file_path,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/imports", response_model=list[navigation.ImportView])
def imports(
    repository_id: PositiveId,
    snapshot_id: PositiveId,
    session: Database,
    file_path: FilePath,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[navigation.ImportView]:
    return navigation.get_imports(
        session, repository_id, snapshot_id, file_path, limit=limit, offset=offset
    )


@router.get("/importers", response_model=list[navigation.ImportView])
def importers(
    repository_id: PositiveId,
    snapshot_id: PositiveId,
    session: Database,
    file_path: FilePath,
    limit: Limit = 100,
    offset: Offset = 0,
) -> list[navigation.ImportView]:
    return navigation.get_imports(
        session,
        repository_id,
        snapshot_id,
        file_path,
        reverse=True,
        limit=limit,
        offset=offset,
    )
