from pathlib import Path

import pytest
from test_broker_runtime import FakeExecutor
from test_resolution_workspace import golden_files

from repopilot.agent.tools import RunScope
from repopilot.config import Settings
from repopilot.resolution.broker_client import BrokerClient, create_executor
from repopilot.resolution.broker_transport import read_token
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxExecutor
from repopilot.resolution.workspace import Workspace


def test_token_is_bounded_and_supports_windows_line_endings(tmp_path):
    path = tmp_path / "token"
    path.write_bytes(b"a" * 64 + b"\r\n")
    assert read_token(path) == "a" * 64
    path.write_bytes(b"a" * 64 + b" ")
    with pytest.raises(ValueError):
        read_token(path)
    path.write_bytes(b"a" * 100)
    with pytest.raises(ValueError):
        read_token(path)


@pytest.mark.parametrize(
    "attack",
    [None, "revision", "source_hash", "image_id", "profile_hash", "unavailable"],
)
def test_client_checks_exact_evidence_and_never_falls_back(
    tmp_path, monkeypatch, attack
):
    token = tmp_path / "token"
    token.write_text("a" * 64)
    executor = FakeExecutor()
    profile = load_profile("fee-days")
    with Workspace(RunScope(1, 1), golden_files()) as workspace:
        result = executor.run(workspace, profile)
        result.command = ["python", "-I", "-B", "/opt/repopilot/run_tests.py"]
        if attack and attack != "unavailable":
            setattr(result, attack, 1 if attack == "revision" else "invalid")

        class Connection:
            status = 200

            def __init__(self, path):
                pass

            def request(self, *args):
                if attack == "unavailable":
                    raise OSError("private diagnostic")

            def getresponse(self):
                return self

            def read(self, limit):
                return result.model_dump_json().encode()

            def close(self):
                pass

        monkeypatch.setattr(
            "repopilot.resolution.broker_client.UnixConnection", Connection
        )
        monkeypatch.setattr(
            SandboxExecutor, "run", lambda *args: pytest.fail("Host fallback forbidden")
        )
        observed = BrokerClient(executor.image_id, tmp_path / "broker.sock", token).run(
            workspace, profile
        )
        assert observed.passed == (attack is None)
        if attack:
            assert (
                observed.infrastructure_error
                and "private" not in observed.model_dump_json()
            )


def test_operator_broker_pair_is_explicit_and_factory_uses_it(tmp_path):
    values = {"_env_file": None, "database_url": "postgresql+psycopg://x@localhost/x"}
    with pytest.raises(ValueError):
        Settings(**values, sandbox_broker_socket=tmp_path / "socket")
    with pytest.raises(ValueError):
        Settings(
            **values,
            sandbox_broker_socket=Path("relative"),
            sandbox_broker_token_file=tmp_path / "token",
        )
    settings = Settings(
        **values,
        resolution_sandbox_image=FakeExecutor.image_id,
        sandbox_broker_socket=tmp_path / "socket",
        sandbox_broker_token_file=tmp_path / "token",
    )
    assert isinstance(create_executor(settings), BrokerClient)
