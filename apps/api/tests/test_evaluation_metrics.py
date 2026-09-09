import pytest

from repopilot.evaluation.metrics import EvidenceIdentity, calculate_metrics


def test_calculate_hit_recall_and_mrr_at_k() -> None:
    expected = [
        [EvidenceIdentity("a.py", "alpha")],
        [EvidenceIdentity("b.py", "beta"), EvidenceIdentity("b.py", "helper")],
        [EvidenceIdentity("c.py")],
    ]
    retrieved = [
        [EvidenceIdentity("x.py"), EvidenceIdentity("a.py", "alpha")],
        [EvidenceIdentity("b.py", "helper"), EvidenceIdentity("z.py")],
        [EvidenceIdentity("z.py"), EvidenceIdentity("y.py")],
    ]

    metrics = calculate_metrics(expected, retrieved, k=2)

    assert metrics.query_count == 3
    assert metrics.hit_rate == pytest.approx(2 / 3)
    assert metrics.recall == pytest.approx(0.5)
    assert metrics.mean_reciprocal_rank == pytest.approx(0.5)


@pytest.mark.parametrize("k", [0, -1])
def test_calculate_metrics_rejects_invalid_k(k: int) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        calculate_metrics([[EvidenceIdentity("a.py")]], [[]], k=k)


def test_calculate_metrics_rejects_misaligned_or_empty_cases() -> None:
    with pytest.raises(ValueError, match="query counts"):
        calculate_metrics([[EvidenceIdentity("a.py")]], [], k=1)
    with pytest.raises(ValueError, match="At least one"):
        calculate_metrics([], [], k=1)
    with pytest.raises(ValueError, match="Every query"):
        calculate_metrics([[]], [[]], k=1)
