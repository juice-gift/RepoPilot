"""Run inside the API container; fixture source is sent as data, executed only by Broker Docker.

The script emits bounded evidence to stdout; redirect it to an evaluation JSON file.
It never imports repository code, chooses commands, or accesses the Docker daemon.
"""

import copy
import json
import shutil
import socket
import threading
import time
from pathlib import Path
from uuid import uuid4

from repopilot.config import Settings
from repopilot.resolution.broker_client import create_executor
from repopilot.resolution.broker_protocol import BrokerRequest
from repopilot.resolution.broker_transport import UnixConnection, read_token
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.workspace import SavedSource, Workspace, digest
from repopilot.agent.tools import RunScope

settings = Settings()
assert not Path("/var/run/docker.sock").exists()
assert not Path("/execution").exists()
assert shutil.which("docker") is None
data_root = Path("/app/apps/api/evaluation/trusted_python")
token = read_token(settings.sandbox_broker_token_file)
checks = []
cases = []


def call(body, *, authorization=None, length=None):
    connection = UnixConnection(settings.sandbox_broker_socket)
    try:
        payload = json.dumps(body).encode()
        headers = {"Authorization": "Bearer " + (authorization or token),
                   "Content-Type": "application/json"}
        if length is not None:
            headers["Content-Length"] = str(length)
        connection.request("POST", "/v1/tests", payload, headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read(32001))
    finally:
        connection.close()


for name in ("itsdangerous", "more-itertools"):
    profile = load_profile("trusted-" + name, registry_path=settings.trusted_profile_registry,
                           registry_digest=settings.trusted_profile_registry_sha256)
    baseline = {p: (data_root / name / "repository" / p).read_text(encoding="utf-8")
                for p in profile.expected_sources}
    request = BrokerRequest(request_id=uuid4().hex, workspace_id=uuid4().hex,
                            profile=profile.case_id, profile_hash=profile.fingerprint(),
                            revision=0, baseline=baseline, updates=[]).model_dump()
    if not cases:
        assert call(request, authorization="0" * 64)[0] == 401
        checks.append("unauthorized_401")
        bad = copy.deepcopy(request)
        bad["profile"] = "trusted-unapproved"
        assert call(bad)[0] == 400
        checks.append("unapproved_profile_400")
        bad = copy.deepcopy(request)
        bad.update(revision=1, updates=[{"../../host.py": "pass"}])
        assert call(bad)[0] == 400
        checks.append("path_escape_400")
        assert call({**request, "command": "whoami"})[0] == 400
        checks.append("arbitrary_command_400")
        assert call(request, length=8_000_001)[0] == 400
        checks.append("oversized_frame_400")
    status, result = call(request)
    assert status == 200 and not result["passed"] and result["cleanup_confirmed"]
    assert result["isolation_confirmed"] and result["observed_passed"] == profile.expected_tests - profile.baseline_failures
    assert call(request) == (status, result)
    checks.append(name + "_exact_replay")
    conflicting = {**request, "workspace_id": uuid4().hex}
    assert call(conflicting)[0] == 409
    checks.append(name + "_conflict_409")
    files = [SavedSource(p, text, digest(text), len(text.encode())) for p, text in baseline.items()]
    with Workspace(RunScope(1, 1), files) as workspace:
        path = next(iter(profile.editable_paths))
        if name == "itsdangerous":
            changed = baseline[path].replace("            if age > max_age:", "            if age < 0 or age > max_age:")
        else:
            changed = baseline[path].replace("    windows = windowed(it, window_size)", "    windows = windowed(it, window_size, fillvalue=_marker)")
        workspace.publish({**baseline, path: changed}, 0)
        fixed = create_executor(settings).run(workspace, profile)
        assert fixed.passed, fixed.model_dump_json()
        independent = create_executor(settings).run(workspace, profile)
        assert independent.passed and independent.source_hash == fixed.source_hash
    cases.append({"profile": profile.case_id, "commit": profile.commit_sha,
                  "baseline": result, "fixed": fixed.model_dump(mode="json"),
                  "independent": independent.model_dump(mode="json")})
    if name == "itsdangerous":
        timeout_request = copy.deepcopy(request)
        timeout_request.update(request_id=uuid4().hex, revision=1,
                               updates=[{path: "while True:\n    pass\n" + baseline[path]}])

responses = []
errors = []


def run_timeout():
    try:
        responses.append(call(timeout_request))
    except Exception as error:
        errors.append(type(error).__name__)


worker = threading.Thread(target=run_timeout)
worker.start()
deadline = time.monotonic() + 8
while time.monotonic() < deadline:
    status, _ = call({**timeout_request, "request_id": uuid4().hex, "profile": "trusted-unapproved"})
    if status == 429:
        break
    time.sleep(0.05)
assert status == 429
checks.append("concurrent_admission_429")
worker.join(60)
assert not worker.is_alive() and not errors and len(responses) == 1
status, timed = responses[0]
assert status == 200 and timed["timed_out"] and not timed["passed"] and timed["cleanup_confirmed"]
checks.append("real_test_timeout_and_cleanup")
assert not Path("/var/run/docker.sock").exists() and shutil.which("docker") is None
checks.append("api_no_daemon_cli_or_execution_volume")
print(json.dumps({"mode": "api-container-to-authenticated-broker-real-docker", "checks": checks,
                  "cases": cases, "timeout": timed}, indent=2))
