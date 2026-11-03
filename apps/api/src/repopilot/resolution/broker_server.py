"""Linux-only constrained Broker entry point. All policy is operator-owned."""

import json
import os
import re
import shutil
import signal
import stat
from pathlib import Path, PurePosixPath

from repopilot.diagnostics import configure_logging, event
from repopilot.resolution.broker_runtime import BrokerRuntime, MappedSandboxExecutor
from repopilot.resolution.broker_transport import BrokerServer, read_token
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxError, docker
from repopilot.resolution.trusted_profiles import read_registry
from repopilot.resolution.workspace import WorkspaceError

DATA = Path("/execution")
SOCKET = Path("/run/repopilot/broker.sock")
TOKEN = Path("/run/secrets/broker_token")
POLICY = Path("/policy/profiles.json")


def inspect_boundary(
    container: dict, volume: dict, project: str, docker_root: str, *, ipc_volume: dict
) -> PurePosixPath:
    """Fail closed unless daemon metadata confirms our private Compose volume."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,62}", project):
        raise SandboxError("Invalid broker deployment identity")
    host, config = container["HostConfig"], container["Config"]
    mounts = {m["Destination"]: m for m in container["Mounts"]}
    labels = config.get("Labels") or {}
    if (
        len(container["Mounts"]) != 5
        or set(mounts)
        != {
            DATA.as_posix(),
            SOCKET.parent.as_posix(),
            TOKEN.as_posix(),
            POLICY.as_posix(),
            "/var/run/docker.sock",
        }
        or config["User"] != "65534:0"
        or host["NetworkMode"] != "none"
        or host["Privileged"]
        or not host["ReadonlyRootfs"]
        or host["CapDrop"] != ["ALL"]
        or host.get("CapAdd")
        or host.get("Devices")
        or host.get("PidMode")
        or host["Memory"] != 268435456
        or host["NanoCpus"] != 1_000_000_000
        or host["PidsLimit"] != 128
        or any("unconfined" in item for item in host["SecurityOpt"])
        or "no-new-privileges:true" not in host["SecurityOpt"]
        and "no-new-privileges=true" not in host["SecurityOpt"]
        or labels.get("com.docker.compose.project") != project
        or labels.get("com.docker.compose.service") != "sandbox-broker"
    ):
        raise SandboxError("Broker service boundary is invalid")
    for target, logical_name in (
        (DATA.as_posix(), "broker-data"),
        (SOCKET.parent.as_posix(), "broker-ipc"),
    ):
        mount = mounts[target]
        if (
            mount["Type"] != "volume"
            or not mount["RW"]
            or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", mount["Name"])
        ):
            raise SandboxError("Broker private volume is invalid")
        metadata = volume if target == DATA.as_posix() else ipc_volume
        expected = str(PurePosixPath(docker_root) / "volumes" / mount["Name"] / "_data")
        if (
            metadata["Name"] != mount["Name"]
            or metadata["Driver"] != "local"
            or metadata["Scope"] != "local"
            or metadata.get("Options")
            or metadata["Mountpoint"] != expected
            or metadata.get("Labels", {}).get("com.docker.compose.project") != project
            or metadata.get("Labels", {}).get("com.docker.compose.volume")
            != logical_name
        ):
            raise SandboxError("Broker private volume ownership is invalid")
    if (
        mounts[TOKEN.as_posix()]["RW"]
        or mounts[TOKEN.as_posix()]["Type"] != "bind"
        or mounts[POLICY.as_posix()]["RW"]
        or mounts[POLICY.as_posix()]["Type"] != "bind"
        or mounts["/var/run/docker.sock"]["Type"] != "bind"
        or mounts["/var/run/docker.sock"]["RW"]
        or mounts["/var/run/docker.sock"]["Source"]
        not in {
            "/var/run/docker.sock",
            "/run/docker.sock",
            # Docker Desktop translates the requested socket into its VM proxy.
            "/run/host-services/docker.proxy.sock",
        }
    ):
        raise SandboxError("Broker credential/daemon mount is invalid")
    root = PurePosixPath(volume["Mountpoint"])
    if (
        not root.is_absolute()
        or ".." in root.parts
        or not PurePosixPath(docker_root).is_absolute()
    ):
        raise SandboxError("Invalid daemon volume path")
    return root


def cleanup_orphans(owner: str, daemon_root: Path, images: set[str]) -> None:
    """Only remove containers proven to be this deployment's restricted tests."""
    ids = docker("ps", "-aq", "--filter", "label=repopilot.broker=" + owner).split()
    if len(ids) > 8:
        raise SandboxError("Broker orphan count requires operator review")
    for identity in ids:
        if not re.fullmatch(r"[a-f0-9]{12,64}", identity):
            raise SandboxError("Invalid broker orphan identity")
        data = json.loads(docker("inspect", identity))[0]
        if (
            not re.fullmatch(r"/repopilot-resolution-[a-f0-9]{32}", data["Name"])
            or data["Image"] not in images
        ):
            raise SandboxError("Broker orphan ownership is ambiguous")
        mounts = data["HostConfig"]["Mounts"]
        if len(mounts) != 2:
            raise SandboxError("Broker orphan mount count is invalid")
        paths = {m["Target"]: Path(m["Source"]) for m in mounts}
        source, validation = paths["/workspace"], paths["/validation"]
        for path in (source, validation):
            if not path.is_relative_to(daemon_root / "workspaces"):
                raise SandboxError("Broker orphan mount escaped its data volume")
        if (
            source.parent != validation.parent
            or source.parent.parent != daemon_root / "workspaces"
            or not re.fullmatch(
                r"repopilot-resolution-[a-z0-9_]{8}", source.parent.name
            )
            or not re.fullmatch(r"source-[0-8]", source.name)
            or not re.fullmatch(r"validation-[a-f0-9]{32}", validation.name)
        ):
            raise SandboxError("Broker orphan workspace identity is invalid")
        # Reuse every existing fixed isolation check before force-removing this ID.
        executor = MappedSandboxExecutor(data["Image"], DATA, daemon_root, owner=owner)
        executor._verify_container(
            data,
            DATA / source.relative_to(daemon_root),
            DATA / validation.relative_to(daemon_root),
        )
        docker("rm", "--force", identity)
    if docker("ps", "-aq", "--filter", "label=repopilot.broker=" + owner).strip():
        raise SandboxError("Broker orphan cleanup could not be confirmed")
    for directory in (DATA / "workspaces").iterdir():
        if (
            not re.fullmatch(r"repopilot-resolution-[a-z0-9_]{8}", directory.name)
            or not directory.is_dir()
            or any(p.is_symlink() for p in (directory, *directory.rglob("*")))
            or not directory.resolve().is_relative_to(DATA / "workspaces")
        ):
            raise WorkspaceError("Broker abandoned workspace requires operator review")
        shutil.rmtree(directory)


def main() -> None:
    import fcntl  # Linux-only; API/Windows imports never require this module.

    os.umask(0o077)
    configure_logging()
    project = os.environ["BROKER_PROJECT"]
    image = os.environ["BROKER_SANDBOX_IMAGE"]
    registry = POLICY
    registry_hash = os.environ["BROKER_PROFILE_REGISTRY_SHA256"]
    approved = read_registry(registry, registry_hash)
    profiles = {
        p.id: load_profile(p.id, registry_path=registry, registry_digest=registry_hash)
        for p in approved.profiles
    }

    # Frozen profiles remain code-owned; trusted profiles are independently loaded above.
    def profile_loader(identity: str):
        if identity.startswith("trusted-"):
            if identity not in profiles:
                raise WorkspaceError("Unknown approved Broker profile")
            return profiles[identity]
        return load_profile(identity)

    MappedSandboxExecutor(image, DATA, DATA)  # validates immutable image syntax
    own_id = os.environ["HOSTNAME"]
    if not re.fullmatch(r"[a-f0-9]{12,64}", own_id):
        raise SandboxError("Broker must run in its private Linux container")
    container = json.loads(docker("inspect", own_id))[0]
    data_mounts = [
        m for m in container["Mounts"] if m["Destination"] == DATA.as_posix()
    ]
    if len(data_mounts) != 1 or data_mounts[0]["Type"] != "volume":
        raise SandboxError("Broker requires its own execution volume")
    volume = json.loads(docker("volume", "inspect", data_mounts[0]["Name"]))[0]
    ipc_mounts = [
        m for m in container["Mounts"] if m["Destination"] == SOCKET.parent.as_posix()
    ]
    if len(ipc_mounts) != 1 or ipc_mounts[0]["Type"] != "volume":
        raise SandboxError("Broker requires a private communication volume")
    ipc_volume = json.loads(docker("volume", "inspect", ipc_mounts[0]["Name"]))[0]
    info = json.loads(docker("info", "--format", "{{json .}}"))
    daemon_root = inspect_boundary(
        container, volume, project, info["DockerRootDir"], ipc_volume=ipc_volume
    )
    for path in (DATA, DATA / "workspaces", DATA / "requests", SOCKET.parent):
        if (
            any(p.is_symlink() for p in (path, *path.parents))
            or not path.is_dir()
            or path.stat().st_uid != os.geteuid()
            or stat.S_IMODE(path.stat().st_mode) != 0o700
        ):
            raise WorkspaceError("Broker directories must be owned regular directories")
    lock_path = DATA / "broker.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    lock = os.fdopen(descriptor, "w")
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    # The process lock is held through socket shutdown and active-job cleanup.
    cleanup_orphans(
        project, daemon_root, {image, *(p.image_id for p in profiles.values())}
    )
    if SOCKET.exists():
        if not stat.S_ISSOCK(SOCKET.lstat().st_mode):
            raise SandboxError("Broker socket path contains an unexpected object")
        SOCKET.unlink()
    runtime = BrokerRuntime(
        load_profile=profile_loader,
        executor_factory=lambda p: MappedSandboxExecutor(
            p.image_id or image, DATA, daemon_root, owner=project
        ),
        ledger=DATA / "requests",
        workspace_parent=DATA / "workspaces",
    )
    with lock, BrokerServer(SOCKET, read_token(TOKEN), runtime) as server:
        event("broker.ready", project=project, transport="private_unix")

        # Raising on SIGTERM unwinds server_close, waits for handlers and keeps the
        # volume lock until their Sandbox finally blocks have finished.
        def terminate(signum, frame):
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, terminate)
        try:
            server.serve_forever(poll_interval=0.25)
        finally:
            SOCKET.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
