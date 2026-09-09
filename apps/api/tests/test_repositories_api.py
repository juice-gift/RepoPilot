from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.db.models import Repository, RepositorySnapshot
from repopilot.ingestion.scanner import ScannedFile, ScanResult, SkippedFile
from repopilot.ingestion.service import IngestionResult
from repopilot.main import create_app


def create_test_client(session: Session, allowed_root: Path) -> TestClient:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/database",
        repository_allowed_root=allowed_root,
        _env_file=None,
    )
    app = create_app(settings=settings)

    def override_database_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_database_session] = override_database_session
    return TestClient(app)


def test_ingest_repository_api_returns_scan_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    now = datetime.now(UTC)
    repository = SimpleNamespace(
        id=1, name="sample", local_path=str(tmp_path / "sample"), created_at=now
    )
    snapshot = SimpleNamespace(
        id=2,
        repository_id=1,
        content_hash="a" * 64,
        source_revision=None,
        accepted_file_count=1,
        skipped_file_count=1,
        total_bytes=10,
        created_at=now,
    )
    scan = ScanResult(
        repository_path=tmp_path / "sample",
        files=(ScannedFile("app.py", "python", "value = 1", "b" * 64, 10),),
        skipped_files=(SkippedFile(".env", "sensitive"),),
        excluded_directories=("node_modules",),
    )
    result = IngestionResult(repository, snapshot, scan, True)
    monkeypatch.setattr(
        "repopilot.api.routes.repositories.ingest_repository", lambda *args, **kwargs: result
    )

    session = MagicMock(spec=Session)
    with create_test_client(session, tmp_path) as client:
        response = client.post(
            "/api/repositories/ingest",
            json={"path": "sample", "name": "sample"},
        )

    assert response.status_code == 201
    assert response.json()["snapshot_created"] is True
    assert response.json()["languages"] == {"python": 1}
    assert response.json()["skipped_reason_counts"] == {"sensitive": 1}
    assert response.json()["skipped_files"] == [
        {"path": ".env", "reason": "sensitive"}
    ]


def test_ingest_repository_api_rejects_outside_path(tmp_path: Path) -> None:
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "app.py").write_text("value = 1\n", encoding="utf-8")

    session = MagicMock(spec=Session)
    with create_test_client(session, allowed_root) as client:
        response = client.post("/api/repositories/ingest", json={"path": str(outside)})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Repository path is outside REPOSITORY_ALLOWED_ROOT"
    }


def test_list_repository_snapshots_returns_not_found(tmp_path: Path) -> None:
    session = MagicMock(spec=Session)
    session.get.return_value = None

    with create_test_client(session, tmp_path) as client:
        response = client.get("/api/repositories/999/snapshots")

    assert response.status_code == 404
    assert response.json() == {"detail": "Repository not found"}


def test_repository_models_expose_expected_table_names() -> None:
    assert Repository.__tablename__ == "repositories"
    assert RepositorySnapshot.__tablename__ == "repository_snapshots"
