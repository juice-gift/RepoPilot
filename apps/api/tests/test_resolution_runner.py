import json

import pytest
from test_agent_runner import ScriptedProvider, call
from test_resolution_workspace import golden_files

from repopilot.agent.tools import RunScope
from repopilot.rag.tool_calling import AgentTurn
from repopilot.resolution.models import ResolutionObservation, ResolutionRequest
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.runner import run_resolution
from repopilot.resolution.sandbox import TestResult
from repopilot.resolution.tools import ResolutionLimits, ResolutionTools, bounded
from repopilot.resolution.workspace import Workspace


class FakeExecutor:
    """Orchestration evidence only. Actual Docker is tested separately."""

    def __init__(self, *codes):
        self.codes = iter(codes)

    def run(self, workspace, profile):
        code = next(self.codes)
        return TestResult(
            workspace_id=workspace.workspace_id,
            revision=workspace.revision,
            profile=profile.case_id,
            exit_code=code,
            stdout="scripted test observation",
            stderr="",
            elapsed_ms=1,
            isolation_confirmed=True,
            cleanup_confirmed=True,
            expected_tests=profile.expected_tests,
            observed_passed=profile.expected_tests if code == 0 else 0,
        )


def plan(decision="repair", files=None):
    return {
        "expected_revision": 0,
        "decision": decision,
        "summary": "Public repair plan"
        if decision == "repair"
        else "Intent cannot be established",
        "steps": ["Read, reproduce, fix, verify"],
        "files": ["fees.py"] if files is None else files,
    }


def fee_patch(
    revision=0, old="min(max(overdue_days - 1, 0), 30)", new="min(overdue_days, 30)"
):
    return {
        "expected_revision": revision,
        "edits": [{"path": "fees.py", "old_text": old, "new_text": new}],
    }


def scenario(*turns, case="fee-days", codes=(), **limits):
    with Workspace(RunScope(1, 2), golden_files()) as workspace:
        root = workspace.root
        tools = ResolutionTools(
            workspace,
            load_profile(case),
            FakeExecutor(*codes),
            ResolutionLimits(**limits),
        )
        result = run_resolution(
            ResolutionRequest(
                repository_id=1,
                snapshot_id=2,
                profile=case,
                issue="Investigate this controlled bug",
            ),
            tools=tools,
            provider=ScriptedProvider(*turns),
        )
    assert not root.exists()
    return result


def test_failure_observation_repair_retest_and_actual_diff():
    incorrect = "min(max(overdue_days - 2, 0), 30)"
    result = scenario(
        call("read_file", {"path": "fees.py"}, "read"),
        call("submit_plan", plan(), "plan"),
        call("run_tests", {"expected_revision": 0}, "baseline"),
        call("apply_patch", fee_patch(new=incorrect), "patch1"),
        call("run_tests", {"expected_revision": 1}, "failed"),
        call("apply_patch", fee_patch(1, old=incorrect), "patch2"),
        call("run_tests", {"expected_revision": 2}, "verified"),
        AgentTurn(text="Repaired and verified against independent tests."),
        codes=(1, 1, 0),
    )
    assert (
        result.repair_status == "verified_repair"
        and result.execution_status == "completed"
    )
    assert [t.revision for t in result.test_results] == [0, 1, 2]
    assert len(result.patch_history) == 2 and "min(overdue_days, 30)" in result.patch
    assert result.diagnostics.patch_attempts == 2


def test_plan_and_failing_baseline_required_before_writes():
    result = scenario(
        call("apply_patch", fee_patch(), "no_plan"),
        call("submit_plan", plan(), "not_read"),
        call("read_file", {"path": "fees.py"}, "read"),
        call("submit_plan", plan(), "plan"),
        call("apply_patch", fee_patch(), "no_baseline"),
        AgentTurn(text="Insufficient evidence."),
    )
    assert not result.patch and result.revision == 0
    assert [s.observation.status for s in result.trace] == [
        "error",
        "error",
        "ok",
        "ok",
        "error",
    ]
    assert result.repair_status == "insufficient_evidence"


def test_ambiguous_case_refuses_and_injection_cannot_expand_permissions():
    result = scenario(
        call("submit_plan", plan(files=["policy.py"]), "unsafeplan"),
        call("apply_patch", fee_patch(), "write"),
        call("run_shell", {"command": "whoami"}, "shell"),
        call("submit_plan", plan("needs_owner_decision", []), "refuse"),
        AgentTurn(text="Owner must decide whether 60 or 300 seconds is intended."),
        case="ambiguous-cap",
    )
    assert result.repair_status == "needs_owner_decision" and not result.patch
    assert result.trace[2].observation.error_code == "unknown_tool"


@pytest.mark.parametrize(
    "turn,expected",
    [
        (AgentTurn(text=""), "invalid_model_response"),
        (AgentTurn(text="x" * 16001), "model_output_limit"),
        (RuntimeError("secret provider response"), "provider_failure"),
    ],
)
def test_provider_failures_bounded_and_private(turn, expected):
    result = scenario(turn)
    assert (
        result.stop_reason == expected
        and "secret provider response" not in result.model_dump_json()
    )


def test_model_patch_test_time_and_context_budgets():
    result = scenario(call("list_files", {"limit": 5}, "list"), model_turns=1)
    assert result.stop_reason == "max_steps"
    result = scenario(
        call("apply_patch", fee_patch(), "denied"),
        call("apply_patch", fee_patch(), "exhausted"),
        patch_attempts=1,
    )
    assert (
        result.stop_reason == "patch_limit" and result.diagnostics.patch_attempts == 1
    )
    result = scenario(
        call("run_tests", {"expected_revision": 0}, "baseline"),
        call("run_tests", {"expected_revision": 0}, "again"),
        test_executions=1,
        codes=(1,),
    )
    assert result.stop_reason == "test_limit" and len(result.test_results) == 1
    result = scenario(AgentTurn(text="Must never be called"), wall_seconds=1)
    assert (
        result.stop_reason == "wall_time_limit" and result.diagnostics.model_calls == 0
    )
    result = scenario(AgentTurn(text="Must never be called"), context_characters=1000)
    assert result.stop_reason == "context_limit" and result.diagnostics.model_calls == 0


def test_current_revision_verification_required_and_final_text_not_proof():
    result = scenario(AgentTurn(text="The issue is fixed and all tests pass."))
    assert result.repair_status == "insufficient_evidence"
    result = scenario(
        call("read_file", {"path": "fees.py"}, "read"),
        call("submit_plan", plan(), "plan"),
        call("run_tests", {"expected_revision": 0}, "baseline"),
        call("apply_patch", fee_patch(), "patch"),
        AgentTurn(text="Fixed!"),
        codes=(1,),
    )
    assert result.repair_status == "incomplete_repair" and result.patch


def test_complete_json_observation_bound_preserves_useful_prefix():
    observation = bounded(
        ResolutionObservation(payload={"source": '"\\' * 20000}), 1000
    )
    assert observation.truncated and len(observation.model_dump_json()) <= 1000
    assert observation.payload["preview"]
    assert json.loads(observation.model_dump_json())


def test_live_observed_bad_schema_gets_precise_feedback_and_consumes_attempt():
    with Workspace(RunScope(1, 2), golden_files()) as workspace:
        tools = ResolutionTools(
            workspace,
            load_profile("fee-days"),
            FakeExecutor(),
            ResolutionLimits(patch_attempts=1),
        )
        schema = next(
            d["parameters"] for d in tools.definitions() if d["name"] == "apply_patch"
        )
        assert "$defs" not in schema
        assert set(schema["properties"]["edits"]["items"]["properties"]) == {
            "path",
            "old_text",
            "new_text",
        }
        raw = json.dumps(
            {
                "expected_revision": 0,
                "edits": [
                    {
                        "description": "replace expression",
                        "old_string": "old",
                        "new_string": "new",
                    }
                ],
            }
        )
        _, observation = tools.execute("apply_patch", raw, remaining_seconds=180)
        assert observation.error_code == "invalid_arguments"
        assert {
            "field": ["edits", 0, "path"],
            "type": "missing",
        } in observation.payload["schema_errors"]
        assert tools.patch_attempts == 1 and workspace.revision == 0
        _, observation = tools.execute("apply_patch", raw, remaining_seconds=180)
        assert observation.error_code == "patch_limit"
