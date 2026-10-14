import json
import os
import shutil

import pytest

from repopilot.config import Settings
from repopilot.evaluation.agent import (
    apply_grounding_reviews,
    evaluate_agent,
    load_agent_dataset,
)
from repopilot.evaluation.runner import DEFAULT_EVALUATION_ROOT


def test_frozen_tasks_are_small_multifile_and_cover_five_tools():
    dataset = load_agent_dataset()
    assert dataset.version == "agent-v3-baseline-1"
    assert len(dataset.tasks) == 3
    assert all(
        len(task.expected_files) >= 2 and len(task.script) >= 2
        for task in dataset.tasks
    )
    assert {call.name for task in dataset.tasks for call in task.script} == {
        "list_files",
        "read_file",
        "search_code",
        "search_symbol",
        "retrieve_context",
    }


@pytest.mark.parametrize("change", ["source", "dataset", "add_file", "traversal"])
def test_frozen_input_changes_fail(tmp_path, change):
    for name in ("agent_manifest.json", "agent_dataset.json"):
        shutil.copyfile(DEFAULT_EVALUATION_ROOT / name, tmp_path / name)
    shutil.copytree(DEFAULT_EVALUATION_ROOT / "agent_golden", tmp_path / "agent_golden")
    if change == "source":
        (tmp_path / "agent_golden/auth.py").write_text(
            "def changed(): pass", encoding="utf-8"
        )
    elif change == "dataset":
        (tmp_path / "agent_dataset.json").write_text("{}", encoding="utf-8")
    elif change == "add_file":
        (tmp_path / "agent_golden/added.py").write_text("x = 1", encoding="utf-8")
    else:
        (tmp_path / "agent_manifest.json").write_text(
            json.dumps({"../outside.py": "hash"}), encoding="utf-8"
        )
    with pytest.raises(ValueError):
        load_agent_dataset(tmp_path)


def test_grounding_is_a_separate_exact_output_review():
    report = {"cases": [{"id": "task", "review_hash": "hash"}]}
    with pytest.raises(ValueError, match="exact answer"):
        apply_grounding_reviews(
            report,
            {"task": {"review_hash": "other", "grounded": True, "reason": "reviewed"}},
        )
    with pytest.raises(ValueError, match="verdict"):
        apply_grounding_reviews(
            report,
            {"task": {"review_hash": "hash", "grounded": "yes", "reason": "reviewed"}},
        )
    apply_grounding_reviews(
        report,
        {
            "task": {
                "review_hash": "hash",
                "grounded": False,
                "reason": "Unsupported claim",
            }
        },
    )
    assert report["cases"][0]["grounded_final_answer"] is False


@pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires migrated PostgreSQL"
)
def test_scripted_frozen_baseline_through_postgres():
    report = evaluate_agent(settings=Settings())
    assert [case["step_count"] for case in report["cases"]] == [3, 5, 6]
    assert all(case["stop_reason"] == "completed" for case in report["cases"])
    assert all(
        case["expected_evidence_found"] and case["multistep"]
        for case in report["cases"]
    )
    assert all(case["grounded_final_answer"] is None for case in report["cases"])
    assert all(not case["invalid_citation_ids"] for case in report["cases"])
