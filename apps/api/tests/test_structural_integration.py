import os
from pathlib import Path

import pytest
from sqlalchemy import delete, select

from repopilot.config import Settings
from repopilot.db.models import CodeSymbol, Repository
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
