import copy
import json
import os
import subprocess
from dataclasses import replace
from types import MappingProxyType

import pytest
from test_resolution_workspace import golden_files, saved

from repopilot.agent.tools import RunScope
from repopilot.resolution.patch import PatchArguments, PatchEngine
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import (
    SandboxError,
    SandboxExecutor,
    docker,
    docker_environment,
)
from repopilot.resolution.workspace import Workspace, digest


def test_image_selection_and_environment_restrict_model_inputs(monkeypatch):
    for image in ("python:latest", "--privileged", "sha256:bad"):
        with pytest.raises(SandboxError):
            SandboxExecutor(image)
    monkeypatch.setenv("OPENAI_API_KEY", "not-forwarded")
    monkeypatch.setenv("DATABASE_URL", "not-forwarded")
    assert (
        "OPENAI_API_KEY" not in docker_environment()
        and "DATABASE_URL" not in docker_environment()
    )


def test_unavailable_runtime_safe_failure(monkeypatch):
    def unavailable(*args, **kwargs):
        raise SandboxError("unavailable")

    monkeypatch.setattr("repopilot.resolution.sandbox.docker", unavailable)
    with Workspace(RunScope(1, 1), golden_files()) as workspace:
        result = SandboxExecutor("sha256:" + "0" * 64).run(
            workspace, load_profile("fee-days")
        )
        assert (
            result.infrastructure_error
            and result.exit_code is None
            and result.cleanup_confirmed
            and not result.passed
        )


@pytest.fixture
def live_image():
    if os.getenv("RUN_SANDBOX_TESTS") != "1":
        pytest.skip("set RUN_SANDBOX_TESTS=1 with the prepared local test image")
    return docker(
        "image", "inspect", "repopilot-tests:v4", "--format", "{{.Id}}"
    ).strip()


def test_live_baseline_patch_independent_tests_and_revision(live_image):
    executor = SandboxExecutor(live_image)
    for case, edits in [
        (
            "fee-days",
            [
                {
                    "path": "fees.py",
                    "old_text": "min(max(overdue_days - 1, 0), 30)",
                    "new_text": "min(overdue_days, 30)",
                }
            ],
        ),
        (
            "dispatch-preconditions",
            [
                {
                    "path": "workflow.py",
                    "old_text": "    delay = retry_delay(attempt, transient)\n    verify_token(token)",
                    "new_text": "    verify_token(token)\n    delay = retry_delay(attempt, transient)",
                },
                {
                    "path": "policy.py",
                    "old_text": '    if not transient:\n        return None\n    if attempt < 0:\n        raise ValueError("Attempt must be nonnegative")',
                    "new_text": '    if attempt < 0:\n        raise ValueError("Attempt must be nonnegative")\n    if not transient:\n        return None',
                },
            ],
        ),
    ]:
        profile = load_profile(case)
        with Workspace(RunScope(1, 1), golden_files()) as workspace:
            baseline = executor.run(workspace, profile)
            assert baseline.infrastructure_error is None, baseline.model_dump_json()
            assert (
                baseline.exit_code == 1
                and baseline.isolation_confirmed
                and baseline.cleanup_confirmed
            )
            assert f"{profile.baseline_failures} failed" in baseline.stdout
            PatchEngine(workspace, profile.editable_paths).apply(
                PatchArguments(expected_revision=0, edits=edits), attempt=1
            )
            result = executor.run(workspace, profile)
            assert result.passed, result.model_dump_json()
            assert result.revision == 1 and baseline.revision == 0
            assert (
                workspace.baseline["fees.py"] != workspace.read("fees.py")
                or case == "dispatch-preconditions"
            )


def controlled_security_profile(source: str, test: str):
    # Engineering-only adversarial fixture; production loader never offers it.
    return replace(
        load_profile("fee-days"),
        expected_tests=1,
        expected_sources=MappingProxyType({"probe.py": digest(source)}),
        validation=MappingProxyType({"test_probe.py": test.encode("utf-8")}),
    )


def test_live_readonly_network_secrets_resources_and_no_docker_socket(
    live_image, monkeypatch
):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "not-forwarded")
    source = "VALUE = 1\n"
    test = """import os, pathlib, socket, resource
import pytest
def test_security():
    assert os.getuid() == 65534
    assert 'DASHSCOPE_API_KEY' not in os.environ
    assert not pathlib.Path('/var/run/docker.sock').exists()
    assert not pathlib.Path('/host').exists()
    for path in ['/workspace/probe.py', '/validation/test_probe.py', '/etc/passwd']:
        with pytest.raises(OSError):
            pathlib.Path(path).write_text('modified')
    with socket.socket() as sock:
        sock.settimeout(1)
        with pytest.raises(OSError):
            sock.connect(('1.1.1.1', 443))
    assert resource.getrlimit(resource.RLIMIT_NOFILE) == (256, 256)
"""
    profile = controlled_security_profile(source, test)
    with Workspace(RunScope(1, 1), [saved("probe.py", source)]) as workspace:
        result = SandboxExecutor(live_image).run(workspace, profile)
        assert result.passed, result.model_dump_json()
        assert workspace.read("probe.py") == source


def test_live_timeout_kills_container_and_output_is_bounded(live_image):
    source = "VALUE = 1\n"
    test = """import os, time
def test_forever():
    for i in range(3000):
        os.write(1, b'x' * 1024)
        os.write(2, b'y' * 1024)
    time.sleep(90)
"""
    profile = controlled_security_profile(source, test)
    with Workspace(RunScope(1, 1), [saved("probe.py", source)]) as workspace:
        result = SandboxExecutor(live_image, timeout_seconds=10).run(workspace, profile)
        root = workspace.root
        assert result.timed_out and result.cleanup_confirmed and not result.passed, (
            result.model_dump_json()
        )
        assert (
            result.truncated
            and len(result.stdout) <= 8000
            and len(result.stderr) <= 8000
        )
    assert not root.exists()
    assert (
        docker(
            "ps", "--all", "--quiet", "--filter", "label=repopilot.resolution=1"
        ).strip()
        == ""
    )


def test_live_inspection_rejects_weakened_security(live_image):
    with Workspace(RunScope(1, 1), golden_files()) as workspace:
        validation = workspace.root / "validation"
        validation.mkdir()
        name = "repopilot-resolution-inspect-test"
        executor = SandboxExecutor(live_image)
        try:
            docker(*executor._create_arguments(name, workspace.source_dir, validation))
            data = json.loads(docker("inspect", name))[0]
            executor._verify_container(data, workspace.source_dir, validation)
            for key, value in [
                ("Privileged", True),
                ("ReadonlyRootfs", False),
                ("NetworkMode", "bridge"),
                ("PidsLimit", 0),
                ("Memory", 0),
                ("CapDrop", []),
            ]:
                tampered = copy.deepcopy(data)
                tampered["HostConfig"][key] = value
                with pytest.raises(SandboxError):
                    executor._verify_container(
                        tampered, workspace.source_dir, validation
                    )
        finally:
            subprocess.run(
                ["docker", "rm", "--force", name],
                capture_output=True,
                check=False,
                timeout=10,
            )


def test_live_process_limit_and_memory_limit(live_image):
    source = "VALUE = 1\n"
    test = """import subprocess, sys
def test_process_limit():
    children = []
    try:
        for i in range(80):
            try:
                children.append(subprocess.Popen([sys.executable, '-I', '-c', 'import time; time.sleep(15)']))
            except OSError:
                break
        assert 1 <= len(children) < 64
    finally:
        for child in children:
            child.kill()
        for child in children:
            child.wait()
"""
    with Workspace(RunScope(1, 1), [saved("probe.py", source)]) as workspace:
        result = SandboxExecutor(live_image).run(
            workspace, controlled_security_profile(source, test)
        )
        assert result.passed, result.model_dump_json()
    test = "def test_memory():\n    value = bytearray(400 * 1024 * 1024)\n    assert value\n"
    with Workspace(RunScope(1, 1), [saved("probe.py", source)]) as workspace:
        result = SandboxExecutor(live_image).run(
            workspace, controlled_security_profile(source, test)
        )
        assert not result.passed and result.exit_code != 0 and result.cleanup_confirmed


def test_live_cancellation_cleans_owned_container_and_workspace(
    live_image, monkeypatch
):
    def cancelled(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("repopilot.resolution.sandbox.bounded_start", cancelled)
    with (
        pytest.raises(KeyboardInterrupt),
        Workspace(RunScope(1, 1), golden_files()) as workspace,
    ):
        root = workspace.root
        SandboxExecutor(live_image).run(workspace, load_profile("fee-days"))
    assert not root.exists()
    assert (
        docker(
            "ps", "--all", "--quiet", "--filter", "label=repopilot.resolution=1"
        ).strip()
        == ""
    )
