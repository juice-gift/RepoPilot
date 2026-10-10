import os

import pytest

from repopilot.config import Settings
from repopilot.evaluation.runner import DEFAULT_EVALUATION_ROOT
from repopilot.evaluation.structural import (
    evaluate_structure,
    load_structural_dataset,
    occurrence_metrics,
)


def test_frozen_inputs_and_hand_labeled_structural_expectations() -> None:
    dataset = load_structural_dataset(DEFAULT_EVALUATION_ROOT)
    assert dataset.version == "v2-structural-1"
    assert len(dataset.symbols) == 16
    assert len(dataset.imports) == 5
    assert len(dataset.references) == 21
    assert {r[3] for r in dataset.references} == {"resolved", "unresolved", "ambiguous"}


def test_metrics_penalize_false_confident_resolution_and_duplicates() -> None:
    expected = [("a", "run")]
    actual = [("a", "run"), ("a", "run"), ("b", "wrong")]
    metrics = occurrence_metrics(expected, actual)
    assert metrics["precision"] == 1 / 3
    assert metrics["recall"] == 1


@pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires migrated PostgreSQL"
)
def test_frozen_structure_evaluation_through_persisted_navigation() -> None:
    report = evaluate_structure(Settings().database_url)
    assert report["symbol_count"] == 16
    for metric in (
        "definitions",
        "imports",
        "reference_resolution",
        "reference_occurrences_and_status",
    ):
        assert report[metric]["precision"] == 1.0, report["bad_cases"]
        assert report[metric]["recall"] == 1.0, report["bad_cases"]
    assert all(not failures for failures in report["bad_cases"].values())
    assert report["reference_counts"] == {
        "resolved": 8,
        "unresolved": 12,
        "ambiguous": 1,
    }
