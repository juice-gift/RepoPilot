import os
from pathlib import Path

import pytest

from repopilot.config import Settings
from repopilot.evaluation.runner import evaluate_retrieval

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1",
    reason="set RUN_DATABASE_TESTS=1 to run live PostgreSQL tests",
)


def test_golden_repository_runs_through_real_vector_pipeline() -> None:
    evaluation_root = Path(__file__).resolve().parents[1] / "evaluation"

    report = evaluate_retrieval(
        database_url=Settings().database_url,
        repository_path=evaluation_root / "golden_repository",
        dataset_path=evaluation_root / "dataset.json",
        top_k=5,
    )

    assert report["strategy"] == "exact-vector-only"
    assert report["repository_file_count"] == 8
    assert report["chunk_count"] > report["repository_file_count"]
    assert report["query_count"] == 8
    assert set(report["metrics"]) == {"k=1", "k=3", "k=5"}
    assert all(0 <= metric["hit_rate"] <= 1 for metric in report["metrics"].values())


def test_measured_hybrid_rerank_improves_frozen_golden_dataset() -> None:
    evaluation_root = Path(__file__).resolve().parents[1] / "evaluation"
    settings = Settings()

    baseline = evaluate_retrieval(
        database_url=settings.database_url,
        repository_path=evaluation_root / "golden_repository",
        dataset_path=evaluation_root / "dataset.json",
        top_k=5,
        strategy="vector",
    )
    hybrid = evaluate_retrieval(
        database_url=settings.database_url,
        repository_path=evaluation_root / "golden_repository",
        dataset_path=evaluation_root / "dataset.json",
        top_k=5,
        strategy="hybrid",
    )

    assert hybrid["metrics"]["k=1"]["hit_rate"] > baseline["metrics"]["k=1"][
        "hit_rate"
    ]
    assert hybrid["metrics"]["k=5"]["mean_reciprocal_rank"] > baseline[
        "metrics"
    ]["k=5"]["mean_reciprocal_rank"]
