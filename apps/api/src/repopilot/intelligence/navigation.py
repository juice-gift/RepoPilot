"""Snapshot-scoped SQL navigation, independent of embeddings and generation."""

from typing import Literal

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from repopilot.db.models import CodeReference, CodeSymbol, ImportRelation, SnapshotFile
from repopilot.intelligence.analysis import (
    INDEX_VERSION,
    ResolutionStatus,
    normalize_name,
)
from repopilot.intelligence.service import require_snapshot

SymbolMatch = Literal["exact", "qualified", "normalized"]


class ResourceNotFoundError(ValueError):
    pass


class IndexNotReadyError(ValueError):
    pass


class FileView(BaseModel):
    id: int
    snapshot_id: int
    path: str
    language: str


class SymbolView(BaseModel):
    id: int
    snapshot_id: int
    index_version: str
    file_path: str
    language: str
    kind: str
    name: str
    qualified_name: str
    parent_symbol_id: int | None
    start_line: int
    end_line: int


class DefinitionView(BaseModel):
    symbol: SymbolView
    content: str


class ReferenceView(BaseModel):
    id: int
    snapshot_id: int
    index_version: str
    file_path: str
    name: str
    qualifier: str | None
    line: int
    column: int
    status: ResolutionStatus
    target_symbol_id: int | None
    reason: str


class ImportView(BaseModel):
    id: int
    snapshot_id: int
    index_version: str
    file_path: str
    module: str
    imported_name: str | None
    alias: str | None
    level: int
    line: int
    column: int
    status: ResolutionStatus
    target_file_path: str | None
    reason: str


def _ready(session: Session, repository_id: int, snapshot_id: int) -> None:
    snapshot = require_snapshot(session, repository_id, snapshot_id)
    if snapshot.structural_index_version != INDEX_VERSION:
        raise IndexNotReadyError(
            "Snapshot structural index is not ready for the current version"
        )


def _file(session: Session, snapshot_id: int, path: str) -> SnapshotFile:
    file = session.scalar(
        select(SnapshotFile).where(
            SnapshotFile.snapshot_id == snapshot_id, SnapshotFile.path == path
        )
    )
    if file is None:
        raise ResourceNotFoundError("Snapshot file not found")
    return file


def list_files(
    session: Session,
    repository_id: int,
    snapshot_id: int,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[FileView]:
    require_snapshot(session, repository_id, snapshot_id)
    files = session.scalars(
        select(SnapshotFile)
        .where(SnapshotFile.snapshot_id == snapshot_id)
        .order_by(SnapshotFile.path)
        .offset(offset)
        .limit(limit)
    )
    return [
        FileView(id=f.id, snapshot_id=f.snapshot_id, path=f.path, language=f.language)
        for f in files
    ]


def _symbol_view(symbol: CodeSymbol, path: str) -> SymbolView:
    return SymbolView(
        id=symbol.id,
        snapshot_id=symbol.snapshot_id,
        index_version=symbol.index_version,
        file_path=path,
        language=symbol.language,
        kind=symbol.kind,
        name=symbol.name,
        qualified_name=symbol.qualified_name,
        parent_symbol_id=symbol.parent_symbol_id,
        start_line=symbol.start_line,
        end_line=symbol.end_line,
    )


def search_symbols(
    session: Session,
    repository_id: int,
    snapshot_id: int,
    *,
    query: str | None = None,
    match: SymbolMatch = "exact",
    file_path: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SymbolView]:
    _ready(session, repository_id, snapshot_id)
    statement = (
        select(CodeSymbol, SnapshotFile.path)
        .join(SnapshotFile, SnapshotFile.id == CodeSymbol.snapshot_file_id)
        .where(
            CodeSymbol.snapshot_id == snapshot_id,
            CodeSymbol.index_version == INDEX_VERSION,
        )
    )
    if file_path is not None:
        statement = statement.where(
            CodeSymbol.snapshot_file_id == _file(session, snapshot_id, file_path).id
        )
    if query is not None:
        if match == "exact":
            statement = statement.where(
                or_(CodeSymbol.name == query, CodeSymbol.qualified_name == query)
            )
        elif match == "qualified":
            statement = statement.where(CodeSymbol.qualified_name == query)
        else:
            statement = statement.where(
                CodeSymbol.normalized_name == normalize_name(query)
            )
    rows = session.execute(
        statement.order_by(SnapshotFile.path, CodeSymbol.start_line, CodeSymbol.id)
        .offset(offset)
        .limit(limit)
    )
    return [_symbol_view(symbol, path) for symbol, path in rows]


def get_definition(
    session: Session, repository_id: int, snapshot_id: int, symbol_id: int
) -> DefinitionView:
    _ready(session, repository_id, snapshot_id)
    row = session.execute(
        select(CodeSymbol, SnapshotFile)
        .join(SnapshotFile, SnapshotFile.id == CodeSymbol.snapshot_file_id)
        .where(
            CodeSymbol.id == symbol_id,
            CodeSymbol.snapshot_id == snapshot_id,
            CodeSymbol.index_version == INDEX_VERSION,
        )
    ).first()
    if row is None:
        raise ResourceNotFoundError("Snapshot symbol not found")
    symbol, file = row
    return DefinitionView(
        symbol=_symbol_view(symbol, file.path),
        content="\n".join(
            file.content.splitlines()[symbol.start_line - 1 : symbol.end_line]
        ),
    )


def find_references(
    session: Session,
    repository_id: int,
    snapshot_id: int,
    *,
    symbol_id: int | None = None,
    file_path: str | None = None,
    status: ResolutionStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ReferenceView]:
    _ready(session, repository_id, snapshot_id)
    statement = (
        select(CodeReference, SnapshotFile.path)
        .join(SnapshotFile, SnapshotFile.id == CodeReference.snapshot_file_id)
        .where(
            CodeReference.snapshot_id == snapshot_id,
            CodeReference.index_version == INDEX_VERSION,
        )
    )
    if symbol_id is not None:
        get_definition(session, repository_id, snapshot_id, symbol_id)
        statement = statement.where(
            CodeReference.target_symbol_id == symbol_id,
            CodeReference.status == "resolved",
        )
    if file_path is not None:
        statement = statement.where(
            CodeReference.snapshot_file_id == _file(session, snapshot_id, file_path).id
        )
    if status is not None:
        statement = statement.where(CodeReference.status == status)
    rows = session.execute(
        statement.order_by(
            SnapshotFile.path,
            CodeReference.line,
            CodeReference.column_number,
            CodeReference.id,
        )
        .offset(offset)
        .limit(limit)
    )
    return [
        ReferenceView(
            id=r.id,
            snapshot_id=r.snapshot_id,
            index_version=r.index_version,
            file_path=path,
            name=r.name,
            qualifier=r.qualifier,
            line=r.line,
            column=r.column_number,
            status=r.status,
            target_symbol_id=r.target_symbol_id,
            reason=r.reason,
        )
        for r, path in rows
    ]


def get_imports(
    session: Session,
    repository_id: int,
    snapshot_id: int,
    file_path: str,
    *,
    reverse: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[ImportView]:
    _ready(session, repository_id, snapshot_id)
    file = _file(session, snapshot_id, file_path)
    target = SnapshotFile.__table__.alias("target_file")
    statement = (
        select(ImportRelation, SnapshotFile.path, target.c.path)
        .join(SnapshotFile, SnapshotFile.id == ImportRelation.snapshot_file_id)
        .outerjoin(target, target.c.id == ImportRelation.target_file_id)
        .where(
            ImportRelation.snapshot_id == snapshot_id,
            ImportRelation.index_version == INDEX_VERSION,
        )
    )
    statement = (
        statement.where(ImportRelation.target_file_id == file.id)
        if reverse
        else statement.where(ImportRelation.snapshot_file_id == file.id)
    )
    rows = session.execute(
        statement.order_by(
            SnapshotFile.path,
            ImportRelation.line,
            ImportRelation.column_number,
            ImportRelation.id,
        )
        .offset(offset)
        .limit(limit)
    )
    return [
        ImportView(
            id=r.id,
            snapshot_id=r.snapshot_id,
            index_version=r.index_version,
            file_path=source,
            module=r.module,
            imported_name=r.imported_name,
            alias=r.alias,
            level=r.level,
            line=r.line,
            column=r.column_number,
            status=r.status,
            target_file_path=destination,
            reason=r.reason,
        )
        for r, source, destination in rows
    ]
