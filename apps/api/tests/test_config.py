from pathlib import Path

import pytest
from pydantic import ValidationError

from repopilot.config import REPOSITORY_ROOT, Settings


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


def test_settings_include_safe_qwen_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/database",
    )

    settings = Settings(_env_file=None)

    assert settings.qwen_embedding_model == "qwen3.7-text-embedding"
    assert settings.qwen_generation_model == "qwen3.7-flash"
    assert settings.embedding_dimensions == 512
    assert settings.dashscope_base_url.endswith("/compatible-mode/v1")
    assert settings.dashscope_api_key is None


def test_settings_resolve_repository_allowed_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/database",
    )
    monkeypatch.setenv("REPOSITORY_ALLOWED_ROOT", str(tmp_path / ".." / tmp_path.name))

    settings = Settings(_env_file=None)

    assert settings.repository_allowed_root == tmp_path.resolve()


def test_settings_resolve_relative_repository_root_from_project_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/database",
    )
    monkeypatch.setenv("REPOSITORY_ALLOWED_ROOT", ".")

    settings = Settings(_env_file=None)

    assert settings.repository_allowed_root == REPOSITORY_ROOT


def test_settings_reject_non_psycopg_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///database.db")

    with pytest.raises(ValidationError, match=r"postgresql\+psycopg"):
        Settings(_env_file=None)


def test_deployment_rejects_implicit_development_defaults() -> None:
    with pytest.raises(ValidationError, match="Deployment requires explicit settings"):
        Settings(
            _env_file=None,
            environment="deployment",
            database_url="postgresql+psycopg://user:password@localhost/database",
        )


def test_deployment_requires_explicit_external_model_and_credential(tmp_path) -> None:
    values = {
        "environment": "deployment",
        "database_url": "postgresql+psycopg://user:password@database/database",
        "frontend_origin": "http://localhost:8080",
        "repository_allowed_root": tmp_path,
        "embedding_dimensions": 512,
        "embedding_provider": "deterministic",
        "generation_provider": "deterministic",
    }
    assert Settings(_env_file=None, **values).environment == "deployment"
    values["generation_provider"] = "openai"
    with pytest.raises(ValidationError, match="explicit models and credentials"):
        Settings(_env_file=None, **values, openai_api_key=None)
