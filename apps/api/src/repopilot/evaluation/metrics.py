from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceIdentity:
    file_path: str
    symbol_name: str | None = None


@dataclass(frozen=True)
class RetrievalMetrics:
    query_count: int
    k: int
    hit_rate: float
    recall: float
    mean_reciprocal_rank: float


def evidence_matches(
    expected: EvidenceIdentity, retrieved: EvidenceIdentity
) -> bool:
    if expected.file_path != retrieved.file_path:
        return False
    return expected.symbol_name is None or expected.symbol_name == retrieved.symbol_name


def calculate_metrics(
    expected_by_query: Sequence[Sequence[EvidenceIdentity]],
    retrieved_by_query: Sequence[Sequence[EvidenceIdentity]],
    *,
    k: int,
) -> RetrievalMetrics:
    if len(expected_by_query) != len(retrieved_by_query):
        raise ValueError("Expected and retrieved query counts must match")
    if not expected_by_query:
        raise ValueError("At least one evaluation query is required")
    if k < 1:
        raise ValueError("k must be at least 1")
    if any(not expected for expected in expected_by_query):
        raise ValueError("Every query must define expected evidence")

    hits = 0
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    for expected, retrieved in zip(
        expected_by_query, retrieved_by_query, strict=True
    ):
        top_k = retrieved[:k]
        matched_expected = {
            expected_index
            for expected_index, expected_item in enumerate(expected)
            if any(evidence_matches(expected_item, item) for item in top_k)
        }
        hits += bool(matched_expected)
        recalls.append(len(matched_expected) / len(expected))

        first_relevant_rank = next(
            (
                rank
                for rank, item in enumerate(top_k, start=1)
                if any(evidence_matches(expected_item, item) for expected_item in expected)
            ),
            None,
        )
        reciprocal_ranks.append(
            0.0 if first_relevant_rank is None else 1.0 / first_relevant_rank
        )

    query_count = len(expected_by_query)
    return RetrievalMetrics(
        query_count=query_count,
        k=k,
        hit_rate=hits / query_count,
        recall=sum(recalls) / query_count,
        mean_reciprocal_rank=sum(reciprocal_ranks) / query_count,
    )


def first_relevant_rank(
    expected: Sequence[EvidenceIdentity],
    retrieved: Sequence[EvidenceIdentity],
) -> int | None:
    return next(
        (
            rank
            for rank, item in enumerate(retrieved, start=1)
            if any(evidence_matches(expected_item, item) for expected_item in expected)
        ),
        None,
    )
