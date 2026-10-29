import copy
import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.models import Repository, SnapshotFile
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.github.binding import persist_binding
from repopilot.github.client import GitHubMCPError
from repopilot.resolution.profiles import GOLDEN_ROOT, load_profile
from repopilot.resolution.workspace import WorkspaceError


def fixture_data():
    audit = json.loads(
        (REPOSITORY_ROOT / "docs/evaluation/v5-fixture-final-audit.json").read_text()
    )
    audit["repository_id"] = int(uuid4().hex[:12], 16)
    sources = {
        path: (GOLDEN_ROOT / "repository" / path).read_bytes().decode()
        for path in load_profile("fee-days").expected_sources
    }
    return audit, sources


def test_unverified_or_modified_input_rejected_without_database():
    audit, sources = fixture_data()
    audit["status"] = "blocked_fixture_mismatch"
    with pytest.raises(GitHubMCPError, match="fixture_not_verified"):
        persist_binding(None, audit=audit, sources=sources)
    audit["status"] = "passed"
    sources["fees.py"] += "\n# modified"
    with pytest.raises(WorkspaceError):
        persist_binding(None, audit=audit, sources=sources)


@pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires migrated PostgreSQL"
)
def test_bindings_idempotent_distinct_commits_and_atomic_conflicts():
    audit, sources = fixture_data()
    engine = create_database_engine(Settings().database_url)
    factory = create_database_session_factory(engine)
    key = f"github://github.com/repositories/{audit['repository_id']}"
    try:
        with factory() as session:
            first = persist_binding(session, audit=audit, sources=sources)
            assert len(first) == 3
            ids = [binding.id for binding in first]
            snapshot_id = first[0].snapshot_id
            assert all(binding.snapshot_id == snapshot_id for binding in first)
            assert [
                row.id for row in persist_binding(session, audit=audit, sources=sources)
            ] == ids
            # Same bytes at a different immutable commit retain separate provenance.
            second_audit = copy.deepcopy(audit)
            second_audit["actual_commit"] = second_audit["expected_commit"] = "c" * 40
            second = persist_binding(session, audit=second_audit, sources=sources)
            assert {row.id for row in second}.isdisjoint(ids)
            assert all(row.snapshot_id == snapshot_id for row in second)
            # A conflicting binding cannot silently replace the original decision.
            first[1].profile = "fee-days"
            session.commit()
            with pytest.raises(GitHubMCPError, match="binding_conflict"):
                persist_binding(session, audit=audit, sources=sources)
            first[1].profile = "dispatch-preconditions"
            session.commit()
            saved = session.scalar(
                select(SnapshotFile).where(
                    SnapshotFile.snapshot_id == snapshot_id,
                    SnapshotFile.path == "fees.py",
                )
            )
            saved.content = "corrupt"
            session.commit()
            with pytest.raises(
                GitHubMCPError, match="saved_snapshot_integrity_mismatch"
            ):
                persist_binding(session, audit=audit, sources=sources)
        # Invalid later Issue causes rollback of all newly created records.
        invalid = copy.deepcopy(audit)
        invalid["repository_id"] += 1
        invalid["issues"][1]["case"] = "wrong"
        with factory() as session:
            with pytest.raises(GitHubMCPError, match="issue_contract_mismatch"):
                persist_binding(session, audit=invalid, sources=sources)
            assert (
                session.scalar(
                    select(Repository).where(
                        Repository.local_path
                        == f"github://github.com/repositories/{invalid['repository_id']}"
                    )
                )
                is None
            )
    finally:
        with factory() as session:
            session.execute(delete(Repository).where(Repository.local_path == key))
            session.commit()
        engine.dispose()
