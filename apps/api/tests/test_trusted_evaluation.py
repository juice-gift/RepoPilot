"""Grader regressions use saved evidence; live adapter validation is opt-in."""

import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.evaluation.contracts import Task
from repopilot.evaluation.grading import resolution_checks
from repopilot.evaluation.trusted import corpus_source, execute_trusted
from repopilot.resolution.profiles import load_profile


def approved(*, live=False):
    registry = REPOSITORY_ROOT / "apps/api/evaluation/trusted_python/profiles.json"
    if live and os.getenv("TEST_TRUSTED_PROFILE_REGISTRY"):
        registry = Path(os.environ["TEST_TRUSTED_PROFILE_REGISTRY"])
    settings = Settings(
        trusted_profile_registry=registry,
        trusted_profile_registry_sha256=hashlib.sha256(
            registry.read_bytes()
        ).hexdigest(),
    )
    profile = load_profile(
        "trusted-itsdangerous",
        registry_path=registry,
        registry_digest=settings.trusted_profile_registry_sha256,
    )
    task = Task(
        id="python/itsdangerous",
        category="resolution",
        source_id="itsdangerous",
        legacy_id=profile.case_id,
        expected="verified_repair",
    )
    return settings, profile, task


@pytest.mark.parametrize(
    "tamper",
    [None, "revision", "image_id", "profile_hash", "baseline_profile", "cleanup"],
)
def test_independent_trusted_grading_rejects_cross_revision_or_policy_evidence(tamper):
    _, profile, task = approved()
    raw = json.loads(
        (REPOSITORY_ROOT / "docs/evaluation/pre-v8-bound-proposals.json").read_text(
            encoding="utf-8"
        )
    )["cases"][0]["result"]
    case = {
        "result": copy.deepcopy(raw),
        "original_unchanged": True,
        "snapshot_unchanged": True,
        "evaluation_inputs_cleaned": True,
        "independent_final_test": copy.deepcopy(raw["test_results"][-1]),
    }
    if tamper == "revision":
        case["independent_final_test"]["revision"] += 1
    elif tamper in {"image_id", "profile_hash"}:
        case["independent_final_test"][tamper] = "wrong"
    elif tamper == "baseline_profile":
        case["result"]["test_results"][0]["profile_hash"] = "wrong"
    elif tamper == "cleanup":
        case["evaluation_inputs_cleaned"] = False
    result = resolution_checks(task, case, approved_profile=profile)
    assert result.status == ("passed" if tamper is None else "failed")


def test_corpus_requires_exact_approved_source_and_known_profile():
    from dataclasses import replace

    _, profile, _ = approved()
    assert len(corpus_source(profile)) == 9
    with pytest.raises(ValueError, match="reviewed real-world corpus"):
        corpus_source(replace(profile, case_id="trusted-unknown"))


@pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1"
    or os.getenv("RUN_TRUSTED_PYTHON_TESTS") != "1",
    reason="requires live DB and approved trusted Docker image",
)
def test_live_adapter_runs_independent_tests_and_cleans_owned_database_inputs():
    settings, profile, task = approved(live=True)
    result = execute_trusted(settings, profile, task, "scripted")
    assert result.status == "passed", result.model_dump_json()
    assert result.evidence["evaluation_inputs_cleaned"]
    assert (
        result.evidence["original_unchanged"] and result.evidence["snapshot_unchanged"]
    )
    assert result.evidence["independent_final_test"]["passed"]
    assert (
        result.evidence["independent_final_test"]["workspace_id"]
        == result.evidence["result"]["workspace_id"]
    )
