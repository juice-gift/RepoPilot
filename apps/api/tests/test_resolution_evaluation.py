import json
from pathlib import Path

import pytest

from repopilot.evaluation.resolution import (
    CASES,
    ScriptedResolutionProvider,
    review_hash,
)
from repopilot.resolution.profiles import GOLDEN_ROOT, load_profile
from repopilot.resolution.workspace import WorkspaceError


def test_frozen_case_expectations_and_scripts_are_separate_from_live_models():
    assert len(CASES) == 3
    for case in CASES:
        profile = load_profile(case)
        provider = ScriptedResolutionProvider(profile)
        assert provider.provider_name == "scripted"
        turns = list(provider.turns)
        assert turns[-1].text.startswith("Scripted")
        assert any(c.name == "submit_plan" for t in turns for c in t.tool_calls)
        if case == "ambiguous-cap":
            assert not profile.editable_paths
            assert not any(c.name == "apply_patch" for t in turns for c in t.tool_calls)
        else:
            assert profile.baseline_failures > 0 and profile.expected_tests > 0


def test_manifest_tampering_rejected(tmp_path: Path, monkeypatch):
    manifest = json.loads((GOLDEN_ROOT / "manifest.json").read_text(encoding="utf-8"))
    manifest["cases"][0]["editable_paths"] = ["validation/test_fees.py"]
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr("repopilot.resolution.profiles.GOLDEN_ROOT", tmp_path)
    with pytest.raises(WorkspaceError, match="manifest"):
        load_profile("fee-days")


def test_review_hash_binds_exact_result():
    assert review_hash({"patch": "one"}) != review_hash({"patch": "two"})
