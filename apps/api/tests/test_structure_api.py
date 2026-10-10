from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.intelligence.analysis import AnalysisError
from repopilot.intelligence.navigation import IndexNotReadyError, ResourceNotFoundError
from repopilot.intelligence.service import SnapshotNotFoundError
from repopilot.main import create_app


def client_for(session: Session, tmp_path: Path) -> TestClient:
    app = create_app(
        settings=Settings(
            database_url="postgresql+psycopg://user:password@localhost/database",
            repository_allowed_root=tmp_path,
            _env_file=None,
        )
    )

    def override() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_database_session] = override
    return TestClient(app)


@pytest.mark.parametrize(
    "endpoint",
    [
        "symbols?match=fuzzy",
        "symbols?q=",
        "symbols?q=%20",
        "files?limit=0",
        "files?limit=501",
        "files?offset=-1",
        "references?status=guess",
        "imports",
        "imports?file_path=",
    ],
)
def test_invalid_structural_request(endpoint: str, tmp_path: Path) -> None:
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        assert (
            client.get(
                f"/api/repositories/1/snapshots/2/structure/{endpoint}"
            ).status_code
            == 422
        )


@pytest.mark.parametrize(
    "error, status",
    [
        (SnapshotNotFoundError("snapshot missing"), 404),
        (ResourceNotFoundError("symbol missing"), 404),
        (IndexNotReadyError("not indexed"), 409),
    ],
)
def test_query_errors_translate_to_typed_http_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error: ValueError, status: int
) -> None:
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr("repopilot.intelligence.navigation.search_symbols", fail)
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        response = client.get("/api/repositories/1/snapshots/2/structure/symbols")
        assert response.status_code == status
        assert response.json()["detail"] == str(error)


def test_parser_failure_and_empty_symbol_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail(*args, **kwargs):
        raise AnalysisError("app.ts: syntax error")

    monkeypatch.setattr("repopilot.api.routes.structure.index_structure", fail)
    monkeypatch.setattr(
        "repopilot.intelligence.navigation.search_symbols", lambda *args, **kwargs: []
    )
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        assert (
            client.post("/api/repositories/1/snapshots/2/structure/index").status_code
            == 422
        )
        assert (
            client.get("/api/repositories/1/snapshots/2/structure/symbols").json() == []
        )
        assert (
            client.get("/api/repositories/0/snapshots/2/structure/files").status_code
            == 422
        )
        schemas = client.get("/openapi.json").json()["components"]["schemas"]
        assert schemas["ReferenceView"]["properties"]["status"]["enum"] == [
            "resolved",
            "unresolved",
            "ambiguous",
        ]
