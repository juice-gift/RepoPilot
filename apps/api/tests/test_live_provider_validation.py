from pathlib import Path

import pytest

from repopilot.config import Settings
from repopilot.evaluation.live_provider import (
    LiveProviderValidationError,
    run_live_provider_validation,
)


def test_live_provider_validation_requires_key_before_database_access(
    tmp_path: Path,
) -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/database",
        openai_api_key=None,
        _env_file=None,
    )

    with pytest.raises(LiveProviderValidationError, match="OPENAI_API_KEY"):
        run_live_provider_validation(
            settings=settings,
            repository_path=tmp_path / "repository",
            dataset_path=tmp_path / "dataset.json",
            case_id="case",
        )
