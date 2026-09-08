from collections.abc import Iterator
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from repopilot.api.dependencies import get_database_session
from repopilot.config import Settings
from repopilot.main import create_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def create_test_client(session: Session) -> TestClient:
    settings = Settings(_env_file=None)
    app = create_app(settings=settings)

    def override_database_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_database_session] = override_database_session
    return TestClient(app)


def test_database_health_endpoint_returns_ok() -> None:
    session = MagicMock(spec=Session)
    session.execute.return_value.scalar_one.return_value = 1

    with create_test_client(session) as client:
        response = client.get("/api/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "postgresql"}


def test_database_health_endpoint_returns_service_unavailable() -> None:
    session = MagicMock(spec=Session)
    session.execute.side_effect = SQLAlchemyError("connection failed")

    with create_test_client(session) as client:
        response = client.get("/api/health/database")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
