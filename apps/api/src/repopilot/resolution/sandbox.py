"""Local Linux Docker execution only; there is deliberately no shell fallback."""

import json
import os
import re
import subprocess
import threading
from pathlib import Path
from time import monotonic
from uuid import uuid4

from pydantic import BaseModel, computed_field

from repopilot.resolution.profiles import TestProfile
from repopilot.resolution.workspace import Workspace, WorkspaceError

OUTPUT_BYTES = 8000


class SandboxError(RuntimeError):
    pass


class TestResult(BaseModel):
    __test__ = False
    workspace_id: str
    revision: int
    profile: str
    exit_code: int | None
    stdout: str
    stderr: str
    elapsed_ms: float
    timed_out: bool = False
    truncated: bool = False
    infrastructure_error: str | None = None
    isolation_confirmed: bool = False
    cleanup_confirmed: bool = False
    expected_tests: int = 0
    observed_passed: int = 0

    @computed_field
    @property
    def passed(self) -> bool:
        return (
            self.exit_code == 0
            and not self.timed_out
            and self.infrastructure_error is None
            and self.isolation_confirmed
            and self.cleanup_confirmed
            and not self.truncated
            and self.expected_tests > 0
            and self.observed_passed == self.expected_tests
        )


def docker_environment() -> dict[str, str]:
    # Inherit only OS/runtime necessities. Never forward app/provider credentials.
    return {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in {
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "HOME",
            "LOCALAPPDATA",
            "APPDATA",
            "PROGRAMDATA",
            "PROGRAMFILES",
        }
    }


def docker(*arguments: str, timeout: float = 10) -> str:
    result = subprocess.run(
        ["docker", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=docker_environment(),
        check=False,
        timeout=max(0.1, timeout),
    )
    if result.returncode != 0:
        raise SandboxError(
            "Docker operation failed; verify the local Linux engine and prepared image"
        )
    return result.stdout


def bounded_start(name: str, timeout: float) -> tuple[int | None, str, str, bool, bool]:
    process = subprocess.Popen(
        ["docker", "start", "--attach", name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=docker_environment(),
    )
    output = [bytearray(), bytearray()]
    truncated = [False, False]

    def drain(stream, index: int) -> None:
        while block := stream.read(1024):
            remaining = max(0, OUTPUT_BYTES - len(output[index]))
            output[index].extend(block[:remaining])
            if len(block) > remaining:
                truncated[index] = True

    threads = [
        threading.Thread(target=drain, args=(stream, i), daemon=True)
        for i, stream in enumerate((process.stdout, process.stderr))
    ]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        process.wait(timeout=max(0.1, timeout))
    except subprocess.TimeoutExpired:
        timed_out = True
        # Killing only the Docker CLI leaves code running. Remove the exact owned
        # container first, then reap the CLI. Executor also repeats cleanup.
        try:
            docker("rm", "--force", name)
        finally:
            process.kill()
            process.wait(timeout=5)
    except BaseException:
        try:
            docker("rm", "--force", name)
        finally:
            process.kill()
            process.wait(timeout=5)
        raise
    finally:
        for thread in threads:
            thread.join(timeout=5)
        for stream in (process.stdout, process.stderr):
            stream.close()
    return (
        process.returncode,
        *(bytes(data).decode("utf-8", errors="replace") for data in output),
        timed_out,
        any(truncated),
    )


class SandboxExecutor:
    def __init__(self, image_id: str, *, timeout_seconds: float = 20) -> None:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
            raise SandboxError("A prepared immutable sandbox image ID is required")
        if not 0.1 <= timeout_seconds <= 60:
            raise SandboxError("Invalid sandbox timeout")
        self.image_id = image_id
        self.timeout_seconds = timeout_seconds

    def _create_arguments(self, name: str, source: Path, validation: Path) -> list[str]:
        return [
            "create",
            "--name",
            name,
            "--pull",
            "never",
            "--label",
            "repopilot.resolution=1",
            "--network",
            "none",
            "--read-only",
            "--user",
            "65534:65534",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges=true",
            "--memory",
            "256m",
            "--memory-swap",
            "256m",
            "--cpus",
            "1",
            "--pids-limit",
            "64",
            "--ulimit",
            "nofile=256:256",
            "--log-driver",
            "none",
            "--ipc",
            "none",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=32m",
            "--workdir",
            "/tmp",
            "--mount",
            f"type=bind,source={source},target=/workspace,readonly",
            "--mount",
            f"type=bind,source={validation},target=/validation,readonly",
            "--entrypoint",
            "python",
            self.image_id,
            "-I",
            "-B",
            "/opt/repopilot/run_tests.py",
        ]

    def _verify_container(self, data: dict, source: Path, validation: Path) -> None:
        host, config = data["HostConfig"], data["Config"]
        mounts = data["Mounts"]
        expected_mounts = {"/workspace", "/validation"}
        if (
            data["Image"] != self.image_id
            or config["User"] != "65534:65534"
            or config["Entrypoint"] != ["python"]
            or config["Cmd"] != ["-I", "-B", "/opt/repopilot/run_tests.py"]
            or config["WorkingDir"] != "/tmp"
            or host["NetworkMode"] != "none"
            or not host["ReadonlyRootfs"]
            or host["Privileged"]
            or host["CapDrop"] != ["ALL"]
            or host.get("CapAdd")
            or "no-new-privileges=true" not in host["SecurityOpt"]
            or any("unconfined" in item for item in host["SecurityOpt"])
            or host["Memory"] != 268435456
            or host["MemorySwap"] != 268435456
            or host["NanoCpus"] != 1_000_000_000
            or host["PidsLimit"] != 64
            or host["IpcMode"] != "none"
            or host.get("PidMode")
            or host.get("Devices")
            or set(host["Tmpfs"]) != {"/tmp"}
            or "noexec" not in host["Tmpfs"]["/tmp"]
            or len(mounts) != 2
            or {m["Destination"] for m in mounts} != expected_mounts
            or any(m["RW"] or m["Type"] != "bind" for m in mounts)
        ):
            raise SandboxError("Mandatory container isolation was not established")
        # Windows Desktop maps bind source paths to Linux VM paths. Verify the
        # daemon's original request too, rather than guessing translated paths.
        originals = host["Mounts"]
        expected = {"/workspace": str(source), "/validation": str(validation)}
        if len(originals) != 2 or any(
            m["Source"] != expected.get(m["Target"]) or not m["ReadOnly"]
            for m in originals
        ):
            raise SandboxError("Container input mounts do not match the owned run")
        env = dict(item.split("=", 1) for item in config["Env"])
        if any(
            key
            not in {
                "PATH",
                "LANG",
                "GPG_KEY",
                "PYTHON_VERSION",
                "PYTHON_SHA256",
                "PYTHON_PIP_VERSION",
                "PYTHON_SETUPTOOLS_VERSION",
                "PYTHON_GET_PIP_URL",
                "PYTHON_GET_PIP_SHA256",
                "PYTHONDONTWRITEBYTECODE",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
            }
            for key in env
        ):
            raise SandboxError("Unexpected sandbox environment variables")

    def run(self, workspace: Workspace, profile: TestProfile) -> TestResult:
        started = monotonic()
        name = "repopilot-resolution-" + uuid4().hex
        result = TestResult(
            workspace_id=workspace.workspace_id,
            revision=workspace.revision,
            profile=profile.case_id,
            exit_code=None,
            stdout="",
            stderr="",
            elapsed_ms=0,
            expected_tests=profile.expected_tests,
        )
        attempted = False
        validation = workspace.root / ("validation-" + uuid4().hex)

        def invoke(*args: str) -> str:
            remaining = self.timeout_seconds - (monotonic() - started)
            if remaining <= 0:
                result.timed_out = True
                raise SandboxError("Sandbox deadline reached")
            return docker(*args, timeout=min(10, remaining))

        try:
            workspace.verify()
            profile.require_snapshot(workspace.baseline)
            if not profile.validation:
                raise SandboxError("This issue has no executable validation profile")
            endpoint = json.loads(invoke("context", "inspect"))[0]["Endpoints"][
                "docker"
            ]["Host"]
            if not endpoint.startswith(("npipe://", "unix://")):
                raise SandboxError("Only the local Docker engine is permitted")
            info = json.loads(invoke("info", "--format", "{{json .}}"))
            if info["OSType"] != "linux" or not any(
                "seccomp" in option for option in info["SecurityOptions"]
            ):
                raise SandboxError("Linux Docker with seccomp is required")
            validation.mkdir(mode=0o755)
            for filename, content in profile.validation.items():
                if not re.fullmatch(r"test_[a-z_]+\.py", filename):
                    raise SandboxError("Invalid controlled validation filename")
                (validation / filename).write_bytes(content)
            source = workspace.source_dir
            attempted = True
            invoke(*self._create_arguments(name, source, validation))
            container = json.loads(invoke("inspect", name))[0]
            self._verify_container(container, source, validation)
            remaining = self.timeout_seconds - (monotonic() - started)
            if remaining <= 0:
                result.timed_out = True
            else:
                _, result.stdout, result.stderr, result.timed_out, result.truncated = (
                    bounded_start(name, remaining)
                )
                if not result.timed_out:
                    state = json.loads(invoke("inspect", name))[0]["State"]
                    result.exit_code = state["ExitCode"]
                    summaries = re.findall(r"(?:^|\s)(\d+) passed", result.stdout)
                    result.observed_passed = int(summaries[-1]) if summaries else 0
                    if state["Running"] or state["OOMKilled"] or state["Error"]:
                        raise SandboxError(
                            "Test container failed or exceeded resource limits"
                        )
                    result.isolation_confirmed = result.stdout.startswith(
                        "REPOPILOT_ISOLATION="
                    )
                    if not result.isolation_confirmed:
                        raise SandboxError("Runtime isolation preflight failed")
            workspace.verify()
            if any(
                (validation / p).read_bytes() != data
                for p, data in profile.validation.items()
            ):
                raise SandboxError("Independent validation changed")
        except (
            SandboxError,
            WorkspaceError,
            OSError,
            subprocess.SubprocessError,
            ValueError,
            KeyError,
            TypeError,
        ):
            result.infrastructure_error = (
                "Sandbox unavailable or mandatory isolation/verification failed"
            )
        finally:
            if attempted:
                try:
                    # rm is idempotent at this boundary: timeout may already have removed it.
                    existing = docker(
                        "ps", "--all", "--quiet", "--filter", f"name=^/{name}$"
                    )
                    if existing.strip():
                        docker("rm", "--force", name)
                    result.cleanup_confirmed = not docker(
                        "ps", "--all", "--quiet", "--filter", f"name=^/{name}$"
                    ).strip()
                except (SandboxError, OSError, subprocess.SubprocessError):
                    result.infrastructure_error = (
                        "Could not confirm test container cleanup"
                    )
            else:
                result.cleanup_confirmed = True
            result.elapsed_ms = round((monotonic() - started) * 1000, 3)
        return result
