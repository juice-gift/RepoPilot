import re
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    database_url: str = Field(min_length=1)
    frontend_origin: str = Field(default="http://localhost:5173", min_length=1)
    repository_allowed_root: Path = REPOSITORY_ROOT
    embedding_provider: Literal["openai", "qwen", "deterministic"] = "openai"
    embedding_model: str = Field(default="text-embedding-3-small", min_length=1)
    qwen_embedding_model: str = Field(default="qwen3.7-text-embedding", min_length=1)
    embedding_dimensions: int = Field(default=512, ge=1)
    retrieval_strategy: Literal["vector", "hybrid"] = "hybrid"
    openai_api_key: SecretStr | None = None
    dashscope_api_key: SecretStr | None = None
    github_mcp_token: SecretStr | None = Field(default=None, repr=False, exclude=True)
    github_mcp_allowed_repositories: list[str] = Field(
        default_factory=list, max_length=8
    )
    dashscope_base_url: str = Field(
        default=(
            "https://ws-0qeb5e7r8oa2y0s1.cn-beijing.maas.aliyuncs.com/"
            "compatible-mode/v1"
        ),
        min_length=1,
    )
    generation_provider: Literal["openai", "qwen", "deterministic"] = "openai"
    generation_model: str = Field(default="gpt-5.6-luna", min_length=1)
    qwen_generation_model: str = Field(default="qwen3.7-flash", min_length=1)
    generation_max_output_tokens: int = Field(default=1_200, ge=64, le=16_000)
    context_character_limit: int = Field(default=24_000, ge=1_000, le=200_000)
    context_max_evidence: int = Field(default=8, ge=1, le=20)
    agent_max_steps: int = Field(default=12, ge=1, le=30)
    agent_observation_character_limit: int = Field(default=12_000, ge=1_000, le=30_000)
    agent_context_character_limit: int = Field(default=60_000, ge=10_000, le=200_000)
    agent_model_output_character_limit: int = Field(default=12_000, ge=1_000, le=30_000)
    resolution_sandbox_image: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @field_validator("database_url")
    @classmethod
    def require_psycopg_database_url(cls, value: str) -> str:
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError(
                "DATABASE_URL must use the postgresql+psycopg:// SQLAlchemy scheme"
            )
        return value

    @field_validator("github_mcp_allowed_repositories")
    @classmethod
    def canonical_github_repositories(cls, values: list[str]) -> list[str]:
        normalized = []
        for value in values:
            if not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", value
            ):
                raise ValueError("GitHub repositories must be exact owner/repo names")
            if value.split("/")[1] in {".", ".."}:
                raise ValueError("Invalid GitHub repository name")
            normalized.append(value.lower())
        return sorted(set(normalized))

    @field_validator("repository_allowed_root")
    @classmethod
    def resolve_repository_allowed_root(cls, value: Path) -> Path:
        expanded = value.expanduser()
        if not expanded.is_absolute():
            expanded = REPOSITORY_ROOT / expanded
        return expanded.resolve()
