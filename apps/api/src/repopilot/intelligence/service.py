from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from repopilot.db.models import (
    CodeReference,
    CodeSymbol,
    ImportRelation,
    RepositorySnapshot,
    SnapshotFile,
)
from repopilot.intelligence.analysis import (
    INDEX_VERSION,
    AnalysisError,
    analyze_source,
    normalize_name,
)


class SnapshotNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class StructuralIndexResult:
    snapshot_id: int
    index_version: str
    symbol_count: int
    import_count: int
    reference_count: int
    created: bool


def require_snapshot(
    session: Session, repository_id: int, snapshot_id: int
) -> RepositorySnapshot:
    snapshot = session.scalar(
        select(RepositorySnapshot).where(
            RepositorySnapshot.id == snapshot_id,
            RepositorySnapshot.repository_id == repository_id,
        )
    )
    if snapshot is None:
        raise SnapshotNotFoundError("Repository snapshot not found")
    return snapshot


def index_structure(
    session: Session, *, repository_id: int, snapshot_id: int
) -> StructuralIndexResult:
    # A row lock serializes repeated requests for this snapshot without a worker.
    snapshot = session.scalar(
        select(RepositorySnapshot)
        .where(
            RepositorySnapshot.id == snapshot_id,
            RepositorySnapshot.repository_id == repository_id,
        )
        .with_for_update()
    )
    if snapshot is None:
        raise SnapshotNotFoundError("Repository snapshot not found")
    if snapshot.structural_index_version == INDEX_VERSION:
        return _result(session, snapshot_id, False)
    files = session.scalars(
        select(SnapshotFile)
        .where(
            SnapshotFile.snapshot_id == snapshot_id,
        )
        .order_by(SnapshotFile.path)
    ).all()
    analyses = {}
    for file in files:
        try:
            analyses[file.path] = analyze_source(file.content, file.language)
        except AnalysisError as exc:
            raise AnalysisError(f"{file.path}: {exc}") from exc

    # Parse everything before touching a previous index. Savepoint also keeps a
    # persistence failure from exposing a partial replacement to the caller.
    with session.begin_nested():
        for model in (CodeReference, ImportRelation, CodeSymbol):
            session.execute(delete(model).where(model.snapshot_id == snapshot_id))
        for file in files:
            symbols: list[CodeSymbol] = []
            for item in analyses[file.path].symbols:
                symbol = CodeSymbol(
                    snapshot_id=snapshot_id,
                    snapshot_file_id=file.id,
                    index_version=INDEX_VERSION,
                    language=file.language,
                    kind=item.kind,
                    name=item.name,
                    normalized_name=normalize_name(item.name),
                    qualified_name=item.qualified_name,
                    parent_symbol_id=symbols[item.parent].id
                    if item.parent is not None
                    else None,
                    start_line=item.start_line,
                    end_line=item.end_line,
                )
                session.add(symbol)
                session.flush()
                symbols.append(symbol)
        snapshot.structural_index_version = INDEX_VERSION
    session.commit()
    return _result(session, snapshot_id, True)


def _result(session: Session, snapshot_id: int, created: bool) -> StructuralIndexResult:
    from sqlalchemy import func

    counts = [
        session.scalar(
            select(func.count())
            .select_from(model)
            .where(
                model.snapshot_id == snapshot_id,
                model.index_version == INDEX_VERSION,
            )
        )
        or 0
        for model in (CodeSymbol, ImportRelation, CodeReference)
    ]
    return StructuralIndexResult(snapshot_id, INDEX_VERSION, *counts, created)
