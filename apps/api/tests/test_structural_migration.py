"""Migration replay uses a newly created disposable database, never user data."""

import os
import re
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, make_url, text

from repopilot.config import Settings

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires local PostgreSQL"
)


def test_clean_v1_to_v2_migration_and_reversible_schema() -> None:
    database_name = "repopilot_v2_test_" + uuid4().hex
    assert re.fullmatch(r"repopilot_v2_test_[a-f0-9]{32}", database_name)
    url = make_url(Settings().database_url)
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    api_root = Path(__file__).resolve().parents[1]
    env = dict(
        os.environ,
        DATABASE_URL=url.set(database=database_name).render_as_string(
            hide_password=False
        ),
    )

    def alembic(*args: str) -> str:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=api_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout + result.stderr

    created = False
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
            created = True
        alembic("upgrade", "0004_add_vector_index")
        temporary = create_engine(url.set(database=database_name))
        try:
            with temporary.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO repositories (name, local_path) VALUES ('migration sentinel', 'inert-test-path')"
                    )
                )
            alembic("upgrade", "head")
            assert "0007_github_resolution_runs (head)" in alembic("current")
            assert "No new upgrade operations" in alembic("check")
            with temporary.connect() as connection:
                assert (
                    connection.scalar(text("SELECT name FROM repositories"))
                    == "migration sentinel"
                )
                assert (
                    connection.scalar(
                        text("SELECT extname FROM pg_extension WHERE extname='vector'")
                    )
                    == "vector"
                )
            alembic("downgrade", "0004_add_vector_index")
            alembic("upgrade", "head")
            assert "No new upgrade operations" in alembic("check")
        finally:
            temporary.dispose()
    finally:
        if created:
            # Exact unique name of the database created by this test above.
            with admin.connect() as connection:
                connection.execute(
                    text(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=:name AND pid != pg_backend_pid()"
                    ),
                    {"name": database_name},
                )
                connection.execute(text(f'DROP DATABASE "{database_name}"'))
        admin.dispose()
