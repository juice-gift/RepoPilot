import json
import threading

import pytest
from test_broker_protocol import request_data

from repopilot.resolution.broker_protocol import BrokerRequest
from repopilot.resolution.broker_runtime import (
    BrokerBusy,
    BrokerConflict,
    BrokerRuntime,
    MappedSandboxExecutor,
)
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import TestResult
from repopilot.resolution.workspace import WorkspaceError, source_identity


class FakeExecutor:
    image_id = "sha256:" + "1" * 64

    def __init__(self):
        self.calls = 0
        self.paths = []

    def run(self, workspace, profile):
        self.calls += 1
        self.paths.append(workspace.root)
        return TestResult(
            workspace_id=workspace.workspace_id,
            revision=workspace.revision,
            profile=profile.case_id,
            exit_code=0,
            stdout="fake unit evidence",
            stderr="",
            elapsed_ms=1,
            expected_tests=profile.expected_tests,
            observed_passed=profile.expected_tests,
            isolation_confirmed=True,
            cleanup_confirmed=True,
            source_hash=source_identity(workspace.sources()),
            profile_hash=profile.fingerprint(),
            image_id=self.image_id,
        )


def runtime(tmp_path, executor):
    return BrokerRuntime(
        load_profile=load_profile,
        executor_factory=lambda p: executor,
        ledger=tmp_path / "ledger",
    )


def test_replay_is_exact_persistent_and_does_not_execute_twice(tmp_path):
    executor = FakeExecutor()
    request = BrokerRequest.model_validate(request_data())
    first = runtime(tmp_path, executor).run(request)
    second = runtime(tmp_path, executor).run(request)
    assert first == second and executor.calls == 1
    assert all(not path.exists() for path in executor.paths)
    with pytest.raises(BrokerConflict):
        runtime(tmp_path, executor).run(
            request.model_copy(update={"workspace_id": "c" * 32})
        )
    assert executor.calls == 1


def test_ambiguous_crash_marker_never_blindly_reexecutes(tmp_path):
    class Crashed(FakeExecutor):
        def run(self, workspace, profile):
            self.paths.append(workspace.root)
            raise RuntimeError("simulated interruption")

    executor = Crashed()
    request = BrokerRequest.model_validate(request_data())
    with pytest.raises(RuntimeError):
        runtime(tmp_path, executor).run(request)
    with pytest.raises(BrokerConflict):
        runtime(tmp_path, FakeExecutor()).run(request)
    assert not executor.paths[0].exists()


def test_concurrent_admission_rejects_second_job_without_execution(tmp_path):
    entered, release = threading.Event(), threading.Event()

    class Slow(FakeExecutor):
        def run(self, workspace, profile):
            entered.set()
            assert release.wait(5)
            return super().run(workspace, profile)

    executor = Slow()
    broker = runtime(tmp_path, executor)
    request = BrokerRequest.model_validate(request_data())
    errors = []

    def first():
        try:
            broker.run(request)
        except BaseException as error:  # noqa: BLE001 - collect worker failure for assertion in the parent test
            errors.append(error)

    thread = threading.Thread(target=first)
    thread.start()
    try:
        assert entered.wait(5)
        with pytest.raises(BrokerBusy):
            broker.run(request.model_copy(update={"request_id": "d" * 32}))
    finally:
        release.set()
        thread.join(5)
    assert not thread.is_alive() and not errors and executor.calls == 1


def test_cached_identity_tampering_is_rejected(tmp_path):
    request = BrokerRequest.model_validate(request_data())
    runtime(tmp_path, FakeExecutor()).run(request)
    path = tmp_path / "ledger" / (request.request_id + ".json")
    data = json.loads(path.read_text())
    data["result"]["revision"] = 1
    path.write_text(json.dumps(data))
    with pytest.raises(BrokerConflict):
        runtime(tmp_path, FakeExecutor()).run(request)


def test_daemon_mapping_refuses_foreign_paths(tmp_path):
    owned = tmp_path / "owned"
    owned.mkdir()
    executor = MappedSandboxExecutor(FakeExecutor.image_id, owned, tmp_path / "daemon")
    source = owned / "private" / "source-0"
    source.mkdir(parents=True)
    assert executor.daemon_path(source) == tmp_path / "daemon/private/source-0"
    with pytest.raises(WorkspaceError):
        executor.daemon_path(tmp_path / "outside")
