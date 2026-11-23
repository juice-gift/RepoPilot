"""Read-only boundary assertions and reversible restart of the test-owned stack."""

import json
import subprocess
import time
import urllib.request
from pathlib import Path

project = "repopilot-broker-acceptance"
private = Path.home() / "AppData/Local/Temp" / project
compose = ["docker", "compose", "--env-file", str(private / "compose.env"),
           "-f", "compose.yaml", "-f", "compose.app.yaml", "-f", "compose.broker.yaml",
           "-f", str(private / "providers.json"), "--profile", "app"]


def command(arguments):
    return subprocess.check_output(arguments, text=True, encoding="utf-8", timeout=60)


def services():
    result = {}
    for role in ("api", "web", "sandbox-broker", "database"):
        data = json.loads(command(["docker", "inspect", f"{project}-{role}-1"]))[0]
        result[role] = {"image": data["Image"], "user": data["Config"]["User"],
                        "health": data["State"]["Health"]["Status"],
                        "network": data["HostConfig"]["NetworkMode"],
                        "privileged": data["HostConfig"]["Privileged"],
                        "mount_targets": sorted(m["Destination"] for m in data["Mounts"]),
                        "published_ports": data["HostConfig"].get("PortBindings")}
        if role in {"api", "web"}:
            assert result[role]["user"] == "65534:65534"
            assert "/var/run/docker.sock" not in result[role]["mount_targets"]
            assert "/execution" not in result[role]["mount_targets"]
        if role == "sandbox-broker":
            names = {entry.split("=", 1)[0] for entry in data["Config"]["Env"]}
            allowed = {"PATH", "PYTHONPATH", "LANG", "GPG_KEY", "PYTHON_VERSION", "PYTHON_SHA256",
                       "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED", "BROKER_PROJECT",
                       "BROKER_SANDBOX_IMAGE", "BROKER_PROFILE_REGISTRY_SHA256"}
            assert names <= allowed
            result[role]["environment_names"] = sorted(names)
            assert result[role]["network"] == "none" and not result[role]["privileged"]
    return result


def persisted():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    values = {}
    for route in ("bindings", "runs"):
        with opener.open("http://localhost:8082/api/github/" + route, timeout=10) as response:
            rows = json.load(response)
        values[route] = sorted(
            [{k: row[k] for k in (("id", "commit_sha", "snapshot_id") if route == "bindings"
                                 else ("id", "result_hash", "state"))} for row in rows],
            key=lambda row: str(row["id"]),
        )
    return values


before_services, before_data = services(), persisted()
assert all(service["health"] == "healthy" for service in before_services.values())
assert len(before_data["bindings"]) == 2 and len(before_data["runs"]) == 4
probe = "import socket,shutil; assert shutil.which('docker') is None; s=socket.socket(); assert s.connect_ex(('127.0.0.1',8000)) != 0; s.close(); print('private_unix_only_no_docker_cli')"
assert command(["docker", "exec", project + "-api-1", "python", "-c", probe]).strip() == "private_unix_only_no_docker_cli"
assert not command(["docker", "ps", "-aq", "--filter", "label=repopilot.broker=" + project]).strip()
command([*compose, "restart", "web", "api", "sandbox-broker"])
deadline = time.monotonic() + 35
while time.monotonic() < deadline:
    after_services = services()
    if all(service["health"] == "healthy" for service in after_services.values()):
        break
    time.sleep(0.2)
assert all(service["health"] == "healthy" for service in after_services.values())
assert persisted() == before_data
report = {"runtime_commit": command(["git", "rev-parse", "HEAD"]).strip(),
          "checks": ["private_api_unix_transport_only", "no_api_web_daemon_or_execution_mount",
                     "broker_network_none_nonprivileged_no_application_credentials",
                     "all_services_healthy_before_after_restart", "exact_binding_run_hashes_preserved",
                     "no_owned_test_container_residue"],
          "services": after_services, "persisted": before_data, "remote_writes": 0}
Path("docs/evaluation/pre-v8-final-deployment-check.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"checks": report["checks"], "status": "passed"}))
