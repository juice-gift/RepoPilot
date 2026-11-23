import hashlib
import json
import os
from pathlib import Path

import pytest
from test_resolution_workspace import saved

from repopilot.agent.tools import RunScope
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxExecutor
from repopilot.resolution.workspace import Workspace, WorkspaceError, digest


@pytest.mark.skipif(
    os.getenv("RUN_TRUSTED_PYTHON_TESTS") != "1",
    reason="requires approved pre-V8 image and real Docker",
)
@pytest.mark.parametrize("name", ["itsdangerous", "more-itertools"])
def test_live_trusted_full_repair_loop_and_owner_decision(name):
    from repopilot.config import REPOSITORY_ROOT
    from repopilot.rag.tool_calling import AgentTurn, ToolCall
    from repopilot.resolution.models import ResolutionRequest
    from repopilot.resolution.runner import run_resolution
    from repopilot.resolution.tools import ResolutionLimits, ResolutionTools

    root = REPOSITORY_ROOT / "apps/api/evaluation/trusted_python"
    registry = Path(
        os.environ.get("TEST_TRUSTED_PROFILE_REGISTRY", str(root / "profiles.json"))
    )
    profile = load_profile(
        "trusted-" + name,
        registry_path=registry,
        registry_digest=hashlib.sha256(registry.read_bytes()).hexdigest(),
    )
    sources = [
        saved(p, (root / name / "repository" / p).read_text(encoding="utf-8"))
        for p in profile.expected_sources
    ]
    path = next(iter(profile.editable_paths))
    old, new = (
        ("            if age > max_age:", "            if age < 0 or age > max_age:")
        if name == "itsdangerous"
        else (
            "    windows = windowed(it, window_size)",
            "    windows = windowed(it, window_size, fillvalue=_marker)",
        )
    )

    def call(name, args, step):
        return AgentTurn(tool_calls=(ToolCall(str(step), name, json.dumps(args)),))

    class Scripted:
        provider_name = "scripted-test"
        model_name = "deterministic-not-llm"

        def __init__(self, turns):
            self.turns = iter(turns)

        def complete(self, **kwargs):
            return next(self.turns)

    start = 3300 if name == "more-itertools" else 1
    plan = {
        "expected_revision": 0,
        "decision": "repair",
        "summary": "Fix historical issue",
        "steps": ["Read, reproduce, patch, verify"],
        "files": [path],
    }
    with Workspace(RunScope(1, 2), sources) as workspace:
        executor = SandboxExecutor(profile.image_id, timeout_seconds=40)
        tools = ResolutionTools(
            workspace, profile, executor, ResolutionLimits(wall_seconds=180)
        )
        result = run_resolution(
            ResolutionRequest(
                repository_id=1,
                snapshot_id=2,
                profile=profile.case_id,
                issue=profile.issue,
            ),
            tools=tools,
            provider=Scripted(
                [
                    call(
                        "read_file",
                        {"path": path, "start_line": start, "end_line": start + 150},
                        1,
                    ),
                    call("submit_plan", plan, 2),
                    call("run_tests", {"expected_revision": 0}, 3),
                    call(
                        "apply_patch",
                        {
                            "expected_revision": 0,
                            "edits": [{"path": path, "old_text": old, "new_text": new}],
                        },
                        4,
                    ),
                    call("run_tests", {"expected_revision": 1}, 5),
                    AgentTurn(
                        text="Deterministic repair verified with independent Docker tests."
                    ),
                ]
            ),
        )
        assert result.repair_status == "verified_repair", result.model_dump_json()
        assert result.test_results[0].exit_code == 1
        assert (
            result.test_results[-1].passed
            and result.test_results[-1].revision == result.revision
        )
        assert result.test_results[-1].profile_hash == profile.fingerprint()
        # Stale tests cannot authorize an edit; forbidden paths never become eligible.
        _, stale = tools.execute(
            "run_tests", '{"expected_revision":0}', remaining_seconds=100
        )
        assert stale.status == "error" and len(tools.tests) == 2
        _, escaped = tools.execute(
            "apply_patch",
            json.dumps(
                {
                    "expected_revision": 1,
                    "edits": [
                        {"path": "../outside.py", "old_text": "x", "new_text": "y"}
                    ],
                }
            ),
            remaining_seconds=100,
        )
        assert escaped.status == "error" and workspace.revision == 1
    with Workspace(RunScope(1, 2), sources) as workspace:
        tools = ResolutionTools(workspace, profile, executor, ResolutionLimits())
        decision = {**plan, "decision": "needs_owner_decision", "files": []}
        result = run_resolution(
            ResolutionRequest(
                repository_id=1,
                snapshot_id=2,
                profile=profile.case_id,
                issue="Ambiguous request; do not assume policy",
            ),
            tools=tools,
            provider=Scripted(
                [
                    call("submit_plan", decision, 1),
                    AgentTurn(text="Owner decision needed."),
                ]
            ),
        )
        assert result.repair_status == "needs_owner_decision"
        assert not result.patch and not result.test_results and result.revision == 0


def policy() -> dict:
    return {
        "version": 1,
        "profiles": [
            {
                "id": "trusted-example",
                "repository": "example/project",
                "commit_sha": "a" * 40,
                "issue": "Fix approved example",
                "image_id": "sha256:" + "1" * 64,
                "import_root": "src",
                "expected_sources": {"src/app.py": digest("value = 1\n")},
                "editable_paths": ["src/app.py"],
                "validation": {"test_app.py": "def test_app():\n    assert False\n"},
                "expected_tests": 1,
                "baseline_failures": 1,
            }
        ],
    }


def approve(tmp_path, data):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return {
        "registry_path": path,
        "registry_digest": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def test_trusted_profile_needs_exact_policy_and_source(tmp_path):
    with pytest.raises(WorkspaceError):
        load_profile("trusted-example")
    approval = approve(tmp_path, policy())
    profile = load_profile("trusted-example", **approval)
    profile.require_snapshot({"src/app.py": "value = 1\n"})
    with pytest.raises(WorkspaceError):
        profile.require_snapshot({"src/app.py": "value = 2\n"})
    assert isinstance(profile.validation["test_app.py"], bytes)
    approval["registry_path"].write_text("{}", encoding="utf-8")
    with pytest.raises(WorkspaceError):
        load_profile("trusted-example", **approval)


@pytest.mark.parametrize(
    "patch",
    [
        {"shell": "echo unsafe"},
        {"command": ["pytest"]},
        {"image_id": "python:latest"},
        {"import_root": "../host"},
        {"editable_paths": ["tests/test_app.py"]},
        {"expected_sources": {"../app.py": "0" * 64}},
        {"validation": {"../test_app.py": "pass"}},
        {"baseline_failures": 2},
        {"source_evidence_limit": 1_000_001},
    ],
)
def test_operator_policy_rejects_unsupported_execution_and_paths(tmp_path, patch):
    data = policy()
    data["profiles"][0].update(patch)
    with pytest.raises(WorkspaceError):
        load_profile("trusted-example", **approve(tmp_path, data))


def test_approved_image_cannot_be_substituted(tmp_path, monkeypatch):
    profile = load_profile("trusted-example", **approve(tmp_path, policy()))
    calls = []
    monkeypatch.setattr(
        "repopilot.resolution.sandbox.docker", lambda *a, **kw: calls.append(a)
    )
    with Workspace(RunScope(1, 2), [saved("src/app.py", "value = 1\n")]) as workspace:
        result = SandboxExecutor("sha256:" + "2" * 64).run(workspace, profile)
        assert not result.passed and result.infrastructure_error
        assert result.cleanup_confirmed and not calls
        assert result.profile_hash == profile.fingerprint()


def test_changed_validation_invalidates_profile_identity(tmp_path):
    data = policy()
    before = load_profile("trusted-example", **approve(tmp_path, data)).fingerprint()
    data["profiles"][0]["validation"]["test_app.py"] = (
        "def test_app():\n    assert True\n"
    )
    after = load_profile("trusted-example", **approve(tmp_path, data)).fingerprint()
    assert before != after


def test_profile_catalog_exposes_only_approved_allowed_identity(tmp_path):
    from unittest.mock import MagicMock

    from sqlalchemy.orm import Session
    from test_structure_api import client_for

    data = policy()
    data["profiles"][0].update(issue_number=12, original_issue_body="Original issue")
    approval = approve(tmp_path, data)
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        settings = client.app.state.settings
        settings.trusted_profile_registry = None
        assert client.get("/api/github/trusted-profiles").json() == []
        settings.trusted_profile_registry = approval["registry_path"]
        settings.trusted_profile_registry_sha256 = approval["registry_digest"]
        settings.github_mcp_allowed_repositories = []
        assert client.get("/api/github/trusted-profiles").json() == []
        settings.github_mcp_allowed_repositories = ["example/project"]
        response = client.get("/api/github/trusted-profiles")
        assert response.status_code == 200
        assert response.json() == [
            {
                "profile": "trusted-example",
                "repository": "example/project",
                "commit_sha": "a" * 40,
                "issue_number": 12,
            }
        ]
        assert "validation" not in response.text and "image_id" not in response.text
        approval["registry_path"].write_text("{}", encoding="utf-8")
        assert client.get("/api/github/trusted-profiles").status_code == 409


def test_real_large_module_budget_is_explicit_and_default_is_preserved():
    from repopilot.config import REPOSITORY_ROOT
    from repopilot.resolution.patch import PatchArguments, PatchEngine, PatchError

    module = (
        REPOSITORY_ROOT
        / "apps/api/evaluation/trusted_python/more-itertools/repository/more_itertools/more.py"
    )
    text = module.read_text(encoding="utf-8")
    path = "more_itertools/more.py"
    args = PatchArguments(
        expected_revision=0,
        edits=[
            {
                "path": path,
                "old_text": "    windows = windowed(it, window_size)",
                "new_text": "    windows = windowed(it, window_size, fillvalue=_marker)",
            }
        ],
    )
    with Workspace(RunScope(1, 2), [saved(path, text)]) as workspace:
        with pytest.raises(PatchError, match="evidence exceeds"):
            PatchEngine(workspace, frozenset({path})).apply(args, attempt=1)
        assert workspace.revision == 0 and workspace.read(path) == text
        PatchEngine(workspace, frozenset({path}), source_evidence_limit=500_000).apply(
            args, attempt=2
        )
        assert workspace.revision == 1 and workspace.baseline[path] == text
