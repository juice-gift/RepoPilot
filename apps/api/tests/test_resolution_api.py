from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from test_agent_runner import ScriptedProvider
from test_resolution_runner import scenario
from test_structure_api import client_for

from repopilot.intelligence.service import SnapshotNotFoundError
from repopilot.rag.tool_calling import AgentTurn
from repopilot.resolution.workspace import WorkspaceError

PAYLOAD = {
    "repository_id": 1,
    "snapshot_id": 2,
    "profile": "fee-days",
    "issue": "Fix overdue charges",
}


def configured(client):
    client.app.state.settings.resolution_sandbox_image = "sha256:" + "0" * 64


@pytest.mark.parametrize(
    "patch",
    [
        {"profile": "arbitrary-repository"},
        {"issue": " "},
        {"issue": "x" * 4001},
        {"repository_id": 0},
        {"shell": "whoami"},
        {"image": "python:latest"},
        {"editable_paths": ["tests/test_app.py"]},
    ],
)
def test_resolve_rejects_unapproved_contract(tmp_path, patch):
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        assert (
            client.post("/api/agent/resolve", json=PAYLOAD | patch).status_code == 422
        )


def test_sandbox_configuration_required(tmp_path):
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        # Exercise missing configuration even when a live-test image is exported.
        client.app.state.settings.resolution_sandbox_image = None
        response = client.post("/api/agent/resolve", json=PAYLOAD)
        assert response.status_code == 503
        assert "RESOLUTION_SANDBOX_IMAGE" in response.text


@pytest.mark.parametrize(
    "error,status",
    [
        (WorkspaceError("private host path"), 409),
        (SnapshotNotFoundError("missing"), 404),
        (OperationalError("private secret", {}, Exception("private")), 503),
    ],
)
def test_resolution_initial_errors_safe(tmp_path, monkeypatch, error, status):
    monkeypatch.setattr(
        "repopilot.api.routes.resolution.create_agent_provider",
        lambda settings: ScriptedProvider(),
    )
    monkeypatch.setattr(
        "repopilot.api.routes.resolution.resolve_snapshot", MagicMock(side_effect=error)
    )
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        configured(client)
        response = client.post("/api/agent/resolve", json=PAYLOAD)
        assert response.status_code == status and "private" not in response.text


def test_typed_resolution_result_and_investigation_contract_preserved(
    tmp_path, monkeypatch
):
    result = scenario(AgentTurn(text="Insufficient evidence."))
    result.workspace_cleaned = True
    monkeypatch.setattr(
        "repopilot.api.routes.resolution.create_agent_provider",
        lambda settings: ScriptedProvider(),
    )
    monkeypatch.setattr(
        "repopilot.api.routes.resolution.resolve_snapshot",
        lambda *args, **kwargs: result,
    )
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        configured(client)
        response = client.post("/api/agent/resolve", json=PAYLOAD)
        assert response.status_code == 200
        assert response.json()["repair_status"] == "insufficient_evidence"
        assert response.json()["workspace_cleaned"]
        schema = client.get("/openapi.json").json()
        assert "/api/agent/investigate" in schema["paths"]
        assert set(
            schema["components"]["schemas"]["ResolutionRequest"]["properties"]
        ) == {"repository_id", "snapshot_id", "issue", "profile"}
        assert (
            schema["components"]["schemas"]["ResolutionRequest"]["additionalProperties"]
            is False
        )
