import pytest
from pydantic import ValidationError
from repopilot.config import Settings


def test_settings_require_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None)


def test_settings_load_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/database",
    )
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:4173")

    settings = Settings(_env_file=None)

    assert settings.database_url.endswith("/database")
    assert settings.frontend_origin == "http://localhost:4173"


def test_settings_reject_non_psycopg_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///database.db")

    with pytest.raises(ValidationError, match=r"postgresql\+psycopg"):
        Settings(_env_file=None)
