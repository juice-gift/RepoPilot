import re
from collections import Counter
from dataclasses import dataclass
from math import sqrt

from repopilot.indexing.vector_store import VectorSearchRow

VECTOR_WEIGHT = 0.7
LEXICAL_WEIGHT = 0.3

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "at",
        "be",
        "before",
        "by",
        "does",
        "each",
        "for",
        "from",
        "how",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "where",
        "which",
        "with",
    }
)


@dataclass(frozen=True)
class HybridSearchRow:
    vector_row: VectorSearchRow
    score: float
    lexical_score: float


def rerank_hybrid(
    rows: list[VectorSearchRow], *, question: str, limit: int
) -> list[HybridSearchRow]:
    query_tokens = _token_counts(question)
    scored: list[HybridSearchRow] = []
    for row in rows:
        lexical_score = _cosine_similarity(
            query_tokens, _token_counts(row.chunk.embedding_content)
        )
        vector_score = max(0.0, min(1.0, 1.0 - row.distance))
        score = VECTOR_WEIGHT * vector_score + LEXICAL_WEIGHT * lexical_score
        scored.append(HybridSearchRow(row, score, lexical_score))
    return sorted(
        scored,
        key=lambda item: (
            -item.score,
            item.vector_row.distance,
            item.vector_row.chunk.id,
        ),
    )[:limit]


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot_product = sum(count * right[token] for token, count in left.items())
    left_norm = sqrt(sum(count * count for count in left.values()))
    right_norm = sqrt(sum(count * count for count in right.values()))
    return dot_product / (left_norm * right_norm)


def _token_counts(text: str) -> Counter[str]:
    tokens: list[str] = []
    for identifier in re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+", text):
        words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", identifier).replace("_", " ")
        for word in words.lower().split():
            normalized = _normalize_token(word)
            if normalized and normalized not in STOP_WORDS:
                tokens.append(normalized)
    return Counter(tokens)


def _normalize_token(token: str) -> str:
    if len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith(("ed", "es")):
        token = token[:-2]
    elif len(token) > 3 and token.endswith("s"):
        token = token[:-1]
    if len(token) > 4 and token.endswith("y"):
        token = token[:-1]
    return token
