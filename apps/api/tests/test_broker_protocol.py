import copy

import pytest
from pydantic import ValidationError
from test_resolution_workspace import golden_files

from repopilot.agent.tools import RunScope
from repopilot.resolution.broker_protocol import BrokerRequest, validated_revisions
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.workspace import Workspace, WorkspaceError, source_identity


def request_data():
    profile = load_profile("fee-days")
    return {
        "request_id": "a" * 32,
        "workspace_id": "b" * 32,
        "profile": profile.case_id,
        "profile_hash": profile.fingerprint(),
        "revision": 0,
        "baseline": {f.path: f.content for f in golden_files()},
        "updates": [],
    }


@pytest.mark.parametrize(
    "extra", ["command", "image", "mounts", "path", "docker_arguments", "shell"]
)
def test_broker_schema_never_accepts_execution_or_host_path_options(extra):
    with pytest.raises(ValidationError):
        BrokerRequest.model_validate({**request_data(), extra: "untrusted"})


@pytest.mark.parametrize(
    "change", ["profile", "profile_hash", "revision", "baseline", "escape", "tests"]
)
def test_broker_independently_rejects_identity_source_and_path_changes(change):
    data = request_data()
    if change == "profile":
        data["profile"] = "dispatch-preconditions"
    elif change == "profile_hash":
        data["profile_hash"] = "0" * 64
    elif change == "revision":
        data["revision"] = 1
    elif change == "baseline":
        data["baseline"]["fees.py"] += "# changed"
    else:
        data.update(
            revision=1,
            updates=[
                {
                    "../outside.py"
                    if change == "escape"
                    else "tests/test_probe.py": "pass"
                }
            ],
        )
    with pytest.raises(WorkspaceError):
        validated_revisions(
            BrokerRequest.model_validate(data), load_profile("fee-days")
        )


def test_workspace_revision_delta_is_private_and_reconstructs_exact_source():
    data = request_data()
    with Workspace(RunScope(1, 2), golden_files()) as workspace:
        original = workspace.sources()
        modified = copy.deepcopy(original)
        modified["fees.py"] = modified["fees.py"].replace(
            "min(max(overdue_days - 1, 0), 30)", "min(overdue_days, 30)"
        )
        workspace.publish(modified, 0)
        updates = workspace.revision_updates()
        data.update(revision=1, updates=updates)
        states = validated_revisions(
            BrokerRequest.model_validate(data), load_profile("fee-days")
        )
        assert states[0] == original and states[-1] == modified
        assert source_identity(states[-1]) == source_identity(workspace.sources())
        updates[0].clear()
        assert workspace.revision_updates()[0]
