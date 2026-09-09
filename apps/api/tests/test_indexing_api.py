from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.main import create_app


def test_index_api_reports_missing_openai_key(tmp_path: Path) -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/database",
        repository_allowed_root=tmp_path,
        embedding_provider="openai",
        openai_api_key=None,
        _env_file=None,
    )
    app = create_app(settings=settings)
    session = MagicMock(spec=Session)

    def override_database_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_database_session] = override_database_session
    with TestClient(app) as client:
        response = client.post("/api/repositories/1/snapshots/2/index")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
    }
