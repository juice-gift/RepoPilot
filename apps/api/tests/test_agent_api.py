from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from test_agent_runner import ScriptedProvider, call
from test_structure_api import client_for

from repopilot.intelligence.service import SnapshotNotFoundError
from repopilot.rag.generation import GenerationConfigurationError
from repopilot.rag.tool_calling import AgentTurn


@pytest.mark.parametrize(
    "payload",
    [
        {"repository_id": 0, "snapshot_id": 1, "question": "x"},
        {"repository_id": 1, "snapshot_id": 0, "question": "x"},
        {"repository_id": 1, "snapshot_id": 2, "question": "  "},
        {"repository_id": 1, "snapshot_id": 2, "question": "x" * 4001},
        {"repository_id": 1, "snapshot_id": 2, "question": "x", "max_steps": 1000},
    ],
)
def test_invalid_api_request(tmp_path, payload):
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        assert client.post("/api/agent/investigate", json=payload).status_code == 422


def test_real_loop_response_contract(tmp_path, monkeypatch):
    monkeypatch.setattr("repopilot.agent.runner.require_snapshot", MagicMock())
    monkeypatch.setattr("repopilot.agent.tools.require_snapshot", MagicMock())
    monkeypatch.setattr(
        "repopilot.api.routes.agent.create_agent_provider",
        lambda settings: ScriptedProvider(
            call(),
            AgentTurn(text="Definition [E1_1]."),
        ),
    )
    session = MagicMock(spec=Session)
    session.scalar.return_value = SimpleNamespace(
        path="a.py", language="python", content="def run(): pass"
    )
    with client_for(session, tmp_path) as client:
        response = client.post(
            "/api/agent/investigate",
            json={"repository_id": 1, "snapshot_id": 2, "question": "inspect"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stop_reason"] == "completed" and data["total_steps"] == 1
        assert data["trace"][0]["validated_arguments"]["path"] == "a.py"
        assert data["sources"][0]["content"] == "def run(): pass"
        assert data["diagnostics"]["model_calls"] == 2
        openapi = client.get("/openapi.json").json()
        schema = openapi["components"]["schemas"]["AgentRequest"]
        assert schema["additionalProperties"] is False
        assert set(schema["properties"]) == {"repository_id", "snapshot_id", "question"}


@pytest.mark.parametrize(
    "error,expected",
    [
        (SnapshotNotFoundError("Repository snapshot not found"), 404),
        (OperationalError("private connection", {}, Exception("secret")), 503),
    ],
)
def test_initial_resource_failures_do_not_leak(tmp_path, monkeypatch, error, expected):
    monkeypatch.setattr(
        "repopilot.api.routes.agent.create_agent_provider",
        lambda settings: ScriptedProvider(),
    )
    monkeypatch.setattr(
        "repopilot.agent.runner.require_snapshot", MagicMock(side_effect=error)
    )
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        response = client.post(
            "/api/agent/investigate",
            json={"repository_id": 1, "snapshot_id": 2, "question": "inspect"},
        )
        assert response.status_code == expected
        assert "secret" not in response.text and "private" not in response.text


def test_missing_provider_configuration(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "repopilot.api.routes.agent.create_agent_provider",
        MagicMock(
            side_effect=GenerationConfigurationError("DASHSCOPE_API_KEY is required"),
        ),
    )
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        response = client.post(
            "/api/agent/investigate",
            json={"repository_id": 1, "snapshot_id": 2, "question": "inspect"},
        )
        assert response.status_code == 503


def test_provider_failure_returns_inspectable_result(tmp_path, monkeypatch):
    monkeypatch.setattr("repopilot.agent.runner.require_snapshot", MagicMock())
    monkeypatch.setattr(
        "repopilot.api.routes.agent.create_agent_provider",
        lambda settings: ScriptedProvider(RuntimeError("private")),
    )
    with client_for(MagicMock(spec=Session), tmp_path) as client:
        response = client.post(
            "/api/agent/investigate",
            json={"repository_id": 1, "snapshot_id": 2, "question": "inspect"},
        )
        assert response.status_code == 200
        assert response.json()["stop_reason"] == "provider_failure"
        assert "private" not in response.text
