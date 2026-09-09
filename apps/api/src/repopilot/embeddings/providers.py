import re
from collections.abc import Sequence
from hashlib import sha256
from math import sqrt
from typing import Protocol

from openai import OpenAI

from repopilot.config import Settings

EMBEDDING_DIMENSIONS = 512
DETERMINISTIC_EMBEDDING_MODEL = "deterministic-token-hash-v1"


class EmbeddingConfigurationError(ValueError):
    pass


class EmbeddingProvider(Protocol):
    provider_name: str
    model_name: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OpenAIEmbeddingProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str = "text-embedding-3-small",
        dimensions: int = EMBEDDING_DIMENSIONS,
        client: OpenAI | None = None,
    ) -> None:
        if not api_key:
            raise EmbeddingConfigurationError(
                "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
            )
        self.model_name = model_name
        self.dimensions = dimensions
        self._client = client or OpenAI(api_key=api_key)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(
            model=self.model_name,
            input=list(texts),
            dimensions=self.dimensions,
            encoding_format="float",
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        vectors = [list(item.embedding) for item in ordered]
        _validate_vectors(vectors, expected_count=len(texts), dimensions=self.dimensions)
        return vectors


class DeterministicEmbeddingProvider:
    provider_name = "deterministic"
    model_name = DETERMINISTIC_EMBEDDING_MODEL

    def __init__(self, dimensions: int = EMBEDDING_DIMENSIONS) -> None:
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = [self._embed_text(text) for text in texts]
        _validate_vectors(vectors, expected_count=len(texts), dimensions=self.dimensions)
        return vectors

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _tokenize(text)
        for token in tokens:
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for identifier in re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+", text):
        normalized = identifier.lower()
        tokens.append(normalized)
        words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", identifier).replace("_", " ")
        parts = [part.lower() for part in words.split()]
        if len(parts) > 1:
            tokens.extend(parts)
    return tokens


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_dimensions != EMBEDDING_DIMENSIONS:
        raise EmbeddingConfigurationError(
            f"EMBEDDING_DIMENSIONS must be {EMBEDDING_DIMENSIONS} for the current schema"
        )
    if settings.embedding_provider == "deterministic":
        return DeterministicEmbeddingProvider(settings.embedding_dimensions)
    api_key = (
        settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    )
    return OpenAIEmbeddingProvider(
        api_key=api_key,
        model_name=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )


def _validate_vectors(
    vectors: Sequence[Sequence[float]], *, expected_count: int, dimensions: int
) -> None:
    if len(vectors) != expected_count:
        raise ValueError(
            f"Embedding provider returned {len(vectors)} vectors for {expected_count} inputs"
        )
    if any(len(vector) != dimensions for vector in vectors):
        raise ValueError(f"Embedding provider must return {dimensions}-dimensional vectors")
