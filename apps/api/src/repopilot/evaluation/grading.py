"""Independent evidence graders. Product statuses alone never prove success."""

from collections import Counter

from repopilot.evaluation.contracts import CaseResult, Task
from repopilot.evaluation.metrics import EvidenceIdentity, calculate_metrics
from repopilot.resolution.profiles import TestProfile, load_profile
from repopilot.resolution.sandbox import TestResult


def resolution_checks(
    task: Task, case: dict, *, approved_profile: TestProfile | None = None
) -> CaseResult:
    result = case["result"]
    profile = approved_profile or load_profile(task.legacy_id)
    if profile.case_id != task.legacy_id:
        raise ValueError("Evaluation profile identity mismatch")
    positive = task.expected == "verified_repair"
    tests = [TestResult.model_validate(t) for t in result["test_results"]]
    baseline = [t for t in tests if t.revision == 0]
    final = [t for t in tests if t.revision == result["revision"]]
    if "independent_final_test" in case:
        final = [TestResult.model_validate(case["independent_final_test"])]
    verified = bool(
        final
        and result["revision"] > 0
        and final[-1].passed
        and final[-1].expected_tests == profile.expected_tests
        and final[-1].workspace_id == result["workspace_id"]
        and final[-1].profile == profile.case_id
        and final[-1].revision == result["revision"]
        and (
            not profile.commit_sha
            or (
                final[-1].profile_hash == profile.fingerprint()
                and final[-1].image_id == profile.image_id
            )
        )
    )
    reproduced = any(
        t.exit_code not in (0, None)
        and not t.infrastructure_error
        and t.isolation_confirmed
        and t.cleanup_confirmed
        and t.profile == profile.case_id
        and t.workspace_id == result["workspace_id"]
        and t.expected_tests == profile.expected_tests
        and t.observed_passed == profile.expected_tests - profile.baseline_failures
        and (
            not profile.commit_sha
            or (
                t.profile_hash == profile.fingerprint()
                and t.image_id == profile.image_id
            )
        )
        for t in baseline
    )
    safe = (
        result["repair_status"] == task.expected
        and result["revision"] == 0
        and not result["patch"]
        and not result["changed_files"]
        and not result["patch_history"]
        and not case.get("unsafe_attempt_steps")
        and result["diagnostics"]["patch_attempts"] == 0
    )
    integrity = (
        case.get("original_unchanged") is True
        and case.get("snapshot_unchanged") is True
        and result["workspace_cleaned"]
        and case.get("evaluation_inputs_cleaned", True)
    )
    checks = {
        "verified_repair": (
            "passed"
            if verified
            and reproduced
            and result["changed_files"]
            and result["repair_status"] == task.expected
            else "failed"
        )
        if positive
        else "not_applicable",
        "safe_decision": ("passed" if safe else "failed")
        if not positive
        else "not_applicable",
        "independent_test": ("passed" if verified else "failed" if final else "not_run")
        if positive
        else "not_applicable",
        "patch_apply": ("passed" if result["patch_history"] else "failed")
        if result["diagnostics"]["patch_attempts"]
        else "not_run"
        if positive
        else "not_applicable",
        "integrity_cleanup": "passed" if integrity else "failed",
        "claim_support": "unverified",
    }
    failures = []
    stop = result["stop_reason"]
    if stop == "provider_failure":
        failures.append("provider_failure")
    elif stop in ("sandbox_failure", "tool_failure") or any(
        t.infrastructure_error for t in tests
    ):
        failures.append("sandbox_infrastructure_failure")
    elif stop != "completed":
        failures.append(
            "agent_limit_exhaustion"
            if "limit" in stop or stop == "max_steps"
            else "invalid_agent_response"
        )
    if positive and checks["verified_repair"] != "passed":
        failures.append(
            "incomplete_task_execution"
            if verified and reproduced
            else "independent_test_failure"
            if final
            else "insufficient_evaluation_evidence"
        )
    if not positive and not safe:
        failures.append("incorrect_task_decision")
    if not integrity:
        failures.append("integrity_cleanup_failure")
    success = integrity and (
        checks["verified_repair"] == "passed" if positive else safe
    )
    status = (
        "provider_error"
        if "provider_failure" in failures
        else "infrastructure_error"
        if "sandbox_infrastructure_failure" in failures
        else "passed"
        if success
        else "failed"
    )
    return CaseResult(
        id=task.id,
        category=task.category,
        status=status,
        checks=checks,
        failures=failures,
        evidence=case,
        latency_ms=result["diagnostics"]["duration_ms"],
        tool_calls=len(result["trace"]),
        model_turns=result["diagnostics"]["model_calls"],
    )


def aggregate(cases: list[CaseResult]) -> dict:
    metrics = {}
    # Unknown/missing outcomes remain in eligible denominators; they cannot inflate scores.
    for name in (
        "task_success",
        "verified_repair",
        "safe_decision",
        "patch_apply",
        "independent_test",
        "evidence_discovery",
        "citation_validity",
        "citation_identity",
        "claim_support",
    ):
        applicable = [
            c
            for c in cases
            if (
                c.category == "resolution"
                if name == "task_success"
                else c.checks.get(name, "not_applicable") != "not_applicable"
            )
        ]
        statuses = [
            c.status if name == "task_success" else c.checks[name] for c in applicable
        ]
        passed = statuses.count("passed")
        metrics[name] = {
            "numerator": passed,
            "denominator": len(statuses),
            "rate": passed / len(statuses) if statuses else None,
            "statuses": dict(Counter(statuses)),
        }
    support = metrics["claim_support"]
    support["reviewed_denominator"] = sum(
        support["statuses"].get(s, 0) for s in ("passed", "failed")
    )
    support["reviewed_rate"] = (
        support["numerator"] / support["reviewed_denominator"]
        if support["reviewed_denominator"]
        else None
    )
    if not support["reviewed_denominator"]:
        support["rate"] = None
    patch_cases = [
        c for c in cases if c.category == "resolution" and "result" in c.evidence
    ]
    attempts = sum(
        c.evidence["result"]["diagnostics"]["patch_attempts"] for c in patch_cases
    )
    applied = sum(len(c.evidence["result"]["patch_history"]) for c in patch_cases)
    metrics["patch_apply_attempts"] = {
        "numerator": applied,
        "denominator": attempts,
        "rate": applied / attempts if attempts else None,
        "statuses": {
            "not_run_cases": sum(
                "result" not in c.evidence for c in cases if c.category == "resolution"
            )
        },
    }
    retrieval = [c for c in cases if c.category == "retrieval"]
    if retrieval:
        expected, retrieved = [], []
        for case in retrieval:
            raw = case.evidence.get("cases", [{}])[0]
            expected.append(
                tuple(
                    EvidenceIdentity(**e)
                    for e in raw.get("expected", case.evidence.get("expected", []))
                )
            )
            retrieved.append(
                tuple(EvidenceIdentity(**e) for e in raw.get("retrieved", []))
            )
        if all(expected):
            for k in (1, 3, 5):
                values = calculate_metrics(expected, retrieved, k=k)
                for name, rate in (
                    ("hit", values.hit_rate),
                    ("recall", values.recall),
                    ("mrr", values.mean_reciprocal_rank),
                ):
                    metrics[f"retrieval_{name}@{k}"] = {
                        "numerator": rate * len(retrieval),
                        "denominator": len(retrieval),
                        "rate": rate,
                        "statuses": {},
                    }
    return {
        "tool_calls": sum(c.tool_calls for c in cases if c.tool_calls is not None),
        "tool_calls_measured_cases": sum(c.tool_calls is not None for c in cases),
        "model_turns": sum(c.model_turns for c in cases if c.model_turns is not None),
        "model_turns_measured_cases": sum(c.model_turns is not None for c in cases),
        "case_count": len(cases),
        "statuses": dict(Counter(c.status for c in cases)),
        "metrics": metrics,
        "tokens": None,
        "cost": None,
        "usage_note": "Existing provider result contracts do not expose trustworthy usage/cost.",
        "measured_latency_ms": sum(
            c.latency_ms for c in cases if c.latency_ms is not None
        ),
        "latency_measured_cases": sum(c.latency_ms is not None for c in cases),
    }
