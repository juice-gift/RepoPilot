"""Deterministic evaluator regressions; real pipelines covered by opt-in integration."""

import copy
import json
import os

import pytest
from sqlalchemy import select

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.models import Repository
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.evaluation.adapters import citation_identity, owned_inputs
from repopilot.evaluation.contracts import CaseResult, Dataset, digest, load_dataset
from repopilot.evaluation.grading import aggregate, resolution_checks
from repopilot.evaluation.harness import compare, failure_result, run
from repopilot.evaluation.runner import DEFAULT_EVALUATION_ROOT


def task(name):
    return next(t for t in load_dataset().tasks if t.id == name)


def frozen_case(name):
    payload = json.loads(
        (
            REPOSITORY_ROOT / "docs/evaluation/v4-resolution-scripted-report.json"
        ).read_text()
    )
    return copy.deepcopy(next(c for c in payload["cases"] if c["id"] == name))


def test_dataset_frozen_and_complete():
    dataset = load_dataset()
    assert len(dataset.tasks) == 17
    assert len({t.id for t in dataset.tasks}) == 17
    assert (
        digest(dataset.model_dump())
        == (DEFAULT_EVALUATION_ROOT / "v6-dataset.sha256").read_text().strip()
    )


@pytest.mark.parametrize("mutation", ["duplicate", "invalid", "tamper"])
def test_invalid_dataset_rejected(tmp_path, mutation):
    payload = load_dataset().model_dump()
    if mutation == "duplicate":
        payload["tasks"].append(payload["tasks"][0])
    elif mutation == "invalid":
        payload["tasks"][0]["category"] = "arbitrary-execution"
    else:
        payload["tasks"][0]["evidence"] = []
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        load_dataset(path)


def test_tampered_source_and_file_set(tmp_path):
    import shutil

    shutil.copytree(DEFAULT_EVALUATION_ROOT, tmp_path, dirs_exist_ok=True)
    source = tmp_path / "golden_repository/src/settings.py"
    source.write_text(source.read_text() + "\n# changed")
    with pytest.raises(ValueError, match="Frozen input changed"):
        load_dataset(tmp_path / "v6-dataset.json", tmp_path)


def test_category_outcome_contract():
    payload = load_dataset().model_dump()
    payload["tasks"][0]["expected"] = "needs_owner_decision"
    with pytest.raises(ValueError, match="mismatch"):
        Dataset.model_validate(payload)


def test_negative_is_decision_not_repair():
    graded = resolution_checks(
        task("resolution/ambiguous-cap"), frozen_case("ambiguous-cap")
    )
    assert graded.status == "passed"
    assert graded.checks["verified_repair"] == "not_applicable"
    assert graded.checks["independent_test"] == "not_applicable"
    assert aggregate([graded])["metrics"]["verified_repair"]["denominator"] == 0
    assert aggregate([graded])["metrics"]["safe_decision"]["rate"] == 1


@pytest.mark.parametrize(
    "mutation",
    ["missing_tests", "failed_test", "wrong_revision", "wrong_workspace", "no_patch"],
)
def test_applied_patch_does_not_prove_repair(mutation):
    case = frozen_case("fee-days")
    result = case["result"]
    if mutation == "missing_tests":
        result["test_results"] = []
    elif mutation == "failed_test":
        result["test_results"][-1]["exit_code"] = 1
    elif mutation == "wrong_revision":
        result["test_results"][-1]["revision"] = 19
    elif mutation == "wrong_workspace":
        result["test_results"][-1]["workspace_id"] = "other"
    else:
        result["changed_files"] = []
    graded = resolution_checks(task("resolution/fee-days"), case)
    assert graded.status == "failed"
    assert graded.checks["verified_repair"] == "failed"
    assert graded.checks["patch_apply"] == "passed"


def test_unsafe_negative_attempt_fails():
    case = frozen_case("ambiguous-cap")
    case["result"]["diagnostics"]["patch_attempts"] = 1
    assert resolution_checks(task("resolution/ambiguous-cap"), case).status == "failed"


def test_denominators_and_missing_usage():
    passed = resolution_checks(task("resolution/fee-days"), frozen_case("fee-days"))
    missing = failure_result(
        task("resolution/dispatch-preconditions"), ConnectionError()
    )
    metric = aggregate([passed, missing])
    assert metric["metrics"]["task_success"]["rate"] == 0.5
    assert metric["metrics"]["verified_repair"]["denominator"] == 2
    assert metric["tokens"] is None and metric["cost"] is None
    assert aggregate([])["metrics"]["task_success"]["rate"] is None


def test_citation_identity_requires_actual_source(tmp_path):
    (tmp_path / "a.py").write_text("value = 3\n")
    source = {
        "file_path": "a.py",
        "start_line": 1,
        "end_line": 1,
        "content": "value = 3",
    }
    assert citation_identity([source], tmp_path)
    assert not citation_identity([dict(source, content="value = 99")], tmp_path)
    assert not citation_identity([dict(source, file_path="../other.py")], tmp_path)
    assert not citation_identity([], tmp_path)


def test_provider_infrastructure_and_limits_classified():
    case = frozen_case("fee-days")
    case["result"]["stop_reason"] = "provider_failure"
    assert (
        resolution_checks(task("resolution/fee-days"), case).status == "provider_error"
    )
    case["result"]["stop_reason"] = "sandbox_failure"
    assert (
        resolution_checks(task("resolution/fee-days"), case).status
        == "infrastructure_error"
    )
    case["result"]["stop_reason"] = "max_steps"
    assert (
        "agent_limit_exhaustion"
        in resolution_checks(task("resolution/fee-days"), case).failures
    )
    assert (
        failure_result(task("resolution/fee-days"), ConnectionError("SECRET")).evidence[
            "error_type"
        ]
        == "ConnectionError"
    )


def report():
    cases = [CaseResult(id="one", category="resolution", status="unverified")]
    return {
        "schema_version": 1,
        "definitions": "v1",
        "dataset": {"hash": "one"},
        "selection": ["one"],
        "mode": "scripted",
        "runtime": {"model": "script"},
        "complete": True,
        "code_commit": "a",
        "cases": [c.model_dump() for c in cases],
        "aggregate": aggregate(cases),
    }


@pytest.mark.parametrize(
    "key", ["dataset", "selection", "definitions", "runtime", "mode", "complete"]
)
def test_comparison_rejects_incompatibility(key):
    left, right = report(), report()
    right[key] = None
    with pytest.raises(ValueError):
        compare(left, right)


def test_comparison_and_aggregate_integrity():
    assert compare(report(), report())["case_changes"] == []
    other = report()
    other["aggregate"]["case_count"] = 2
    with pytest.raises(ValueError):
        compare(report(), other)


def test_empty_unknown_selection_rejected(tmp_path):
    for selected in ([], ["unknown"], ["retrieval/missing-database-url"] * 2):
        with pytest.raises(ValueError):
            run(
                Settings(),
                mode="scripted",
                output=tmp_path / "out.json",
                selected=selected,
            )


def test_runner_retains_errors_and_never_live_falls_back(tmp_path, monkeypatch):
    from contextlib import contextmanager

    modes = []

    @contextmanager
    def owned(settings):
        yield tmp_path

    def fail(task, settings, mode, strategy, root):
        modes.append(mode)
        raise ConnectionError("DO NOT PERSIST secret")

    monkeypatch.setattr("repopilot.evaluation.harness.owned_inputs", owned)
    monkeypatch.setattr("repopilot.evaluation.harness.execute", fail)
    output = tmp_path / "run.json"
    value = run(Settings(), mode="live", output=output, categories=["resolution"])
    assert modes == ["live"] * 3
    assert len(value["cases"]) == 3
    assert all(c["status"] == "infrastructure_error" for c in value["cases"])
    assert "DO NOT PERSIST" not in output.read_text()
    assert output.with_suffix(".md").exists()


@pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1", reason="requires PostgreSQL"
)
def test_owned_cleanup_on_failure_preserves_existing_rows():
    settings = Settings()
    engine = create_database_engine(settings.database_url)
    factory = create_database_session_factory(engine)
    try:
        with factory() as session:
            before = set(session.scalars(select(Repository.id)))
        with pytest.raises(RuntimeError), owned_inputs(settings) as root:
            with factory() as session:
                session.add(
                    Repository(
                        name="V6 owned test",
                        local_path=str((root / "golden_repository").resolve()),
                    )
                )
                session.commit()
            raise RuntimeError("injected failure")
        assert root is not None and not root.exists()
        with factory() as session:
            assert set(session.scalars(select(Repository.id))) == before
    finally:
        engine.dispose()


def test_exact_reviews_and_historical_failures():
    from repopilot.evaluation.reviews import apply_reviews, historical_evidence

    history = historical_evidence()
    assert len(history) == 9
    assert sum(r.get("supported") is False for r in history[:3]) == 2
    graded = CaseResult(
        id="rag/one",
        category="rag",
        status="unverified",
        checks={"claim_support": "unverified"},
        evidence={"answer": "claim"},
    )
    value = report()
    value["cases"] = [graded.model_dump()]
    review = {
        "id": graded.id,
        "evidence_hash": digest(graded.evidence),
        "supported": False,
        "reviewer": "test reviewer",
        "provenance": "deterministic regression only",
        "reason": "The answer claims unsupported behavior.",
    }
    applied = apply_reviews(value, [review])
    assert applied["cases"][0]["status"] == "failed"
    assert "unsupported_final_claims" in applied["cases"][0]["failures"]
    review["evidence_hash"] = "tampered"
    with pytest.raises(ValueError, match="exact evidence"):
        apply_reviews(value, [review])


def test_aggregate_reuses_retrieval_metrics():
    case = CaseResult(
        id="retrieval/one",
        category="retrieval",
        status="passed",
        evidence={
            "cases": [
                {
                    "expected": [{"file_path": "a", "symbol_name": None}],
                    "retrieved": [
                        {"file_path": "b", "symbol_name": None},
                        {"file_path": "a", "symbol_name": None},
                    ],
                }
            ]
        },
    )
    metrics = aggregate([case])["metrics"]
    assert metrics["retrieval_hit@1"]["rate"] == 0
    assert metrics["retrieval_mrr@5"]["rate"] == 0.5


def test_harness_has_no_remote_write_dependency():
    import ast
    import inspect

    from repopilot.evaluation import adapters, harness

    for module in (adapters, harness):
        tree = ast.parse(inspect.getsource(module))
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        assert not any("github" in (name or "") for name in imports)
