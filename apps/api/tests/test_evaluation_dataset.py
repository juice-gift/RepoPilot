import json
from pathlib import Path

import pytest

from repopilot.evaluation.dataset import load_evaluation_dataset


def test_loads_checked_in_evaluation_dataset() -> None:
    path = Path(__file__).resolve().parents[1] / "evaluation" / "dataset.json"

    dataset = load_evaluation_dataset(path)

    assert dataset.version == 1
    assert len(dataset.cases) == 8
    assert len({case.case_id for case in dataset.cases}) == len(dataset.cases)
    assert all(case.expected_evidence for case in dataset.cases)


def test_rejects_duplicate_case_ids(tmp_path: Path) -> None:
    path = tmp_path / "dataset.json"
    path.write_text(
        json.dumps(
            {
                "name": "duplicate",
                "version": 1,
                "cases": [
                    {
                        "id": "same",
                        "query": "first",
                        "expected_evidence": [{"file_path": "a.py"}],
                    },
                    {
                        "id": "same",
                        "query": "second",
                        "expected_evidence": [{"file_path": "b.py"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate"):
        load_evaluation_dataset(path)
