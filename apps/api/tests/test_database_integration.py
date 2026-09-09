import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from repopilot.config import Settings
from repopilot.db.session import create_database_engine
from repopilot.main import create_app

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="set RUN_DATABASE_TESTS=1 to run live PostgreSQL tests",
)


def test_migrated_database_connectivity_and_pgvector() -> None:
    settings = Settings()
    engine = create_database_engine(settings.database_url)
    app = create_app(settings=settings, database_engine=engine)

    with TestClient(app) as client:
        response = client.get("/api/health/database")

        with engine.connect() as connection:
            migration_revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            pgvector_version = connection.execute(
                text(
                    "SELECT extversion FROM pg_extension "
                    "WHERE extname = 'vector'"
                )
            ).scalar_one()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "postgresql"}
    assert migration_revision == "0001_enable_pgvector"
    assert pgvector_version
