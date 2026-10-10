import os
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from repopilot.config import Settings
from repopilot.db.models import (
    CodeReference,
    CodeSymbol,
    ImportRelation,
    Repository,
    SnapshotFile,
)
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.ingestion.service import ingest_repository
from repopilot.intelligence.analysis import AnalysisError
from repopilot.intelligence.service import SnapshotNotFoundError, index_structure

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires migrated PostgreSQL"
)


def test_symbol_persistence_idempotency_snapshot_content_and_cleanup(
    tmp_path: Path,
) -> None:
    source = tmp_path / "app.py"
    source.write_text(
        "class App:\n    def run(self):\n        return 1\n", encoding="utf-8"
    )
    engine = create_database_engine(Settings().database_url)
    factory = create_database_session_factory(engine)
    try:
        with factory() as session:
            first = ingest_repository(
                session, requested_path=str(tmp_path), allowed_root=tmp_path
            )
            source.write_text("def newer():\n    return 2\n", encoding="utf-8")
            result = index_structure(
                session,
                repository_id=first.repository.id,
                snapshot_id=first.snapshot.id,
            )
            symbols = session.scalars(
                select(CodeSymbol)
                .where(CodeSymbol.snapshot_id == first.snapshot.id)
                .order_by(CodeSymbol.id)
            ).all()
            assert [(s.qualified_name, s.start_line, s.end_line) for s in symbols] == [
                ("App", 1, 3),
                ("App.run", 2, 3),
            ]
            assert symbols[1].parent_symbol_id == symbols[0].id
            assert result.created and result.symbol_count == 2
            again = index_structure(
                session,
                repository_id=first.repository.id,
                snapshot_id=first.snapshot.id,
            )
            assert not again.created
            assert session.scalars(
                select(CodeSymbol.id)
                .where(CodeSymbol.snapshot_id == first.snapshot.id)
                .order_by(CodeSymbol.id)
            ).all() == [s.id for s in symbols]
            second = ingest_repository(
                session, requested_path=str(tmp_path), allowed_root=tmp_path
            )
            index_structure(
                session,
                repository_id=first.repository.id,
                snapshot_id=second.snapshot.id,
            )
            assert session.scalars(
                select(CodeSymbol.name).where(
                    CodeSymbol.snapshot_id == second.snapshot.id
                )
            ).all() == ["newer"]
            with pytest.raises(SnapshotNotFoundError):
                index_structure(
                    session,
                    repository_id=first.repository.id + 99999,
                    snapshot_id=first.snapshot.id,
                )
            source.write_text("def broken(:", encoding="utf-8")
            broken = ingest_repository(
                session, requested_path=str(tmp_path), allowed_root=tmp_path
            )
            with pytest.raises(AnalysisError, match="app.py"):
                index_structure(
                    session,
                    repository_id=first.repository.id,
                    snapshot_id=broken.snapshot.id,
                )
            assert broken.snapshot.structural_index_version is None
            assert (
                session.scalars(
                    select(CodeSymbol).where(
                        CodeSymbol.snapshot_id == broken.snapshot.id
                    )
                ).all()
                == []
            )
            session.execute(
                delete(Repository).where(Repository.id == first.repository.id)
            )
            session.commit()
            assert (
                session.scalars(
                    select(CodeSymbol).where(
                        CodeSymbol.snapshot_id.in_(
                            [first.snapshot.id, second.snapshot.id]
                        )
                    )
                ).all()
                == []
            )
    finally:
        engine.dispose()


def test_cross_file_imports_references_and_database_isolation(tmp_path: Path) -> None:
    (tmp_path / "service.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from service import run as go\ndef dup(): pass\ndef dup(): pass\ngo()\ndup()\nmissing()\n",
        encoding="utf-8",
    )
    (tmp_path / "service.ts").write_text(
        "export const run = () => 1;", encoding="utf-8"
    )
    (tmp_path / "app.ts").write_text(
        "import { run } from './service';\nrun();", encoding="utf-8"
    )
    engine = create_database_engine(Settings().database_url)
    try:
        with create_database_session_factory(engine)() as session:
            first = ingest_repository(
                session, requested_path=str(tmp_path), allowed_root=tmp_path
            )
            sid = first.snapshot.id
            result = index_structure(
                session, repository_id=first.repository.id, snapshot_id=sid
            )
            assert result.import_count == 2
            relations = session.scalars(
                select(ImportRelation).where(ImportRelation.snapshot_id == sid)
            ).all()
            assert {
                session.get(SnapshotFile, r.target_file_id).path for r in relations
            } == {"service.py", "service.ts"}
            assert all(r.status == "resolved" for r in relations)
            refs = session.scalars(
                select(CodeReference).where(CodeReference.snapshot_id == sid)
            ).all()
            assert {r.status for r in refs} == {"resolved", "unresolved", "ambiguous"}
            assert {r.name for r in refs if r.status == "resolved"} == {"go", "run"}
            original_ids = [r.id for r in refs]
            index_structure(session, repository_id=first.repository.id, snapshot_id=sid)
            assert session.scalars(
                select(CodeReference.id)
                .where(CodeReference.snapshot_id == sid)
                .order_by(CodeReference.id)
            ).all() == sorted(original_ids)
            (tmp_path / "service.py").write_text(
                "def different(): return 2", encoding="utf-8"
            )
            second = ingest_repository(
                session, requested_path=str(tmp_path), allowed_root=tmp_path
            )
            index_structure(
                session,
                repository_id=first.repository.id,
                snapshot_id=second.snapshot.id,
            )
            second_go = session.scalar(
                select(CodeReference).where(
                    CodeReference.snapshot_id == second.snapshot.id,
                    CodeReference.name == "go",
                )
            )
            assert (
                second_go.status == "unresolved" and second_go.target_symbol_id is None
            )
            first_target = next(r.target_symbol_id for r in refs if r.name == "go")
            with pytest.raises(IntegrityError), session.begin_nested():
                second_go.status = "resolved"
                second_go.target_symbol_id = first_target
                session.flush()
            first_file = session.scalar(
                select(SnapshotFile).where(SnapshotFile.snapshot_id == sid)
            )
            with pytest.raises(IntegrityError), session.begin_nested():
                session.add(
                    CodeSymbol(
                        snapshot_id=second.snapshot.id,
                        snapshot_file_id=first_file.id,
                        index_version="test",
                        language="python",
                        kind="function",
                        name="bad",
                        normalized_name="bad",
                        qualified_name="bad",
                        start_line=1,
                        end_line=1,
                    )
                )
                session.flush()
            session.execute(
                delete(Repository).where(Repository.id == first.repository.id)
            )
            session.commit()
            for model in (CodeReference, ImportRelation, CodeSymbol):
                assert (
                    session.scalar(
                        select(func.count())
                        .select_from(model)
                        .where(model.snapshot_id.in_([sid, second.snapshot.id]))
                    )
                    == 0
                )
    finally:
        engine.dispose()
