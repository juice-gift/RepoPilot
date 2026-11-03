import copy

import pytest

from repopilot.resolution.broker_server import inspect_boundary
from repopilot.resolution.sandbox import SandboxError


def boundary():
    container = {
        "Config": {
            "User": "65534:0",
            "Labels": {
                "com.docker.compose.project": "probe",
                "com.docker.compose.service": "sandbox-broker",
            },
        },
        "HostConfig": {
            "NetworkMode": "none",
            "Privileged": False,
            "ReadonlyRootfs": True,
            "CapDrop": ["ALL"],
            "SecurityOpt": ["no-new-privileges:true"],
        },
        "Mounts": [
            {
                "Destination": "/execution",
                "Name": "probe_broker-data",
                "Type": "volume",
                "RW": True,
            },
            {
                "Destination": "/run/repopilot",
                "Name": "probe_broker-ipc",
                "Type": "volume",
                "RW": True,
            },
            {"Destination": "/run/secrets/broker_token", "Type": "bind", "RW": False},
            {
                "Destination": "/var/run/docker.sock",
                "Source": "/var/run/docker.sock",
                "Type": "bind",
                "RW": False,
            },
        ],
    }
    volume = {
        "Name": "probe_broker-data",
        "Driver": "local",
        "Scope": "local",
        "Options": None,
        "Mountpoint": "/var/lib/docker/volumes/probe_broker-data/_data",
        "Labels": {
            "com.docker.compose.project": "probe",
            "com.docker.compose.volume": "broker-data",
        },
    }
    return container, volume


def test_broker_maps_only_verified_private_volume():
    container, volume = boundary()
    assert (
        str(inspect_boundary(container, volume, "probe", "/var/lib/docker"))
        == volume["Mountpoint"]
    )


@pytest.mark.parametrize(
    "attack",
    [
        "public",
        "root",
        "privileged",
        "extra_mount",
        "token_write",
        "foreign",
        "driver",
        "options",
        "escape",
        "socket",
    ],
)
def test_broker_rejects_changed_service_or_volume_boundary(attack):
    container, volume = copy.deepcopy(boundary())
    if attack == "public":
        container["HostConfig"]["NetworkMode"] = "bridge"
    elif attack == "root":
        container["Config"]["User"] = "0"
    elif attack == "privileged":
        container["HostConfig"]["Privileged"] = True
    elif attack == "extra_mount":
        container["Mounts"].append({"Destination": "/host"})
    elif attack == "token_write":
        container["Mounts"][2]["RW"] = True
    elif attack == "foreign":
        volume["Labels"]["com.docker.compose.project"] = "other"
    elif attack == "driver":
        volume["Driver"] = "nfs"
    elif attack == "options":
        volume["Options"] = {"device": "/host"}
    elif attack == "escape":
        volume["Mountpoint"] = "/var/lib/docker/volumes/../../host"
    else:
        container["Mounts"][3]["Source"] = "/other.sock"
    with pytest.raises(SandboxError):
        inspect_boundary(container, volume, "probe", "/var/lib/docker")
