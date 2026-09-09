from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from repopilot.config import Settings
from repopilot.embeddings.providers import (
    EMBEDDING_DIMENSIONS,
    DeterministicEmbeddingProvider,
    EmbeddingConfigurationError,
    OpenAIEmbeddingProvider,
    create_embedding_provider,
)


def test_deterministic_embeddings_are_normalized_and_repeatable() -> None:
    provider = DeterministicEmbeddingProvider()

    vectors = provider.embed(["alpha beta alpha", "alpha beta alpha"])

    assert vectors[0] == vectors[1]
    assert len(vectors[0]) == EMBEDDING_DIMENSIONS
    assert sum(value * value for value in vectors[0]) == pytest.approx(1.0)


def test_deterministic_embeddings_split_code_identifiers() -> None:
    provider = DeterministicEmbeddingProvider()
    query, relevant, unrelated = provider.embed(
        ["calculate invoice total", "calculate_invoice_total", "verify_password"]
    )

    def similarity(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right, strict=True))

    assert similarity(query, relevant) > similarity(query, unrelated)


def test_openai_provider_uses_configured_model_and_dimensions() -> None:
    client = MagicMock()
    client.embeddings.create.return_value = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=[2.0] * EMBEDDING_DIMENSIONS),
            SimpleNamespace(index=0, embedding=[1.0] * EMBEDDING_DIMENSIONS),
        ]
    )
    provider = OpenAIEmbeddingProvider(api_key="test", client=client)

    vectors = provider.embed(["first", "second"])

    assert vectors[0][0] == 1.0
    assert vectors[1][0] == 2.0
    client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input=["first", "second"],
        dimensions=EMBEDDING_DIMENSIONS,
        encoding_format="float",
    )


def test_openai_provider_rejects_wrong_vector_dimensions() -> None:
    client = MagicMock()
    client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=[1.0])]
    )
    provider = OpenAIEmbeddingProvider(api_key="test", client=client)

    with pytest.raises(ValueError, match="512-dimensional"):
        provider.embed(["text"])


def test_provider_factory_requires_openai_key() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/database",
        embedding_provider="openai",
        openai_api_key=None,
        _env_file=None,
    )

    with pytest.raises(EmbeddingConfigurationError, match="OPENAI_API_KEY"):
        create_embedding_provider(settings)


def test_provider_factory_rejects_schema_dimension_mismatch() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/database",
        embedding_provider="deterministic",
        embedding_dimensions=64,
        _env_file=None,
    )

    with pytest.raises(EmbeddingConfigurationError, match="must be 512"):
        create_embedding_provider(settings)
