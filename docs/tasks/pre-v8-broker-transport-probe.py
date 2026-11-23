"""Linux API-container adversarial transport/filesystem checks, no source execution."""

import json
import socket
import stat
import tempfile
import time
from pathlib import Path

from repopilot.config import Settings
from repopilot.resolution.broker_runtime import MappedSandboxExecutor
from repopilot.resolution.broker_transport import read_token
from repopilot.resolution.workspace import WorkspaceError

s = Settings()
token = read_token(s.sandbox_broker_token_file)
checks = []


def raw(headers, body=b"", *, delay=False):
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(8)
    try:
        connection.connect(str(s.sandbox_broker_socket))
        started = time.monotonic()
        connection.sendall(("POST /v1/tests HTTP/1.0\r\n" + headers + "\r\n\r\n").encode() + body)
        response = connection.recv(4096)
        if delay:
            assert 4 <= time.monotonic() - started < 7
        return int(response.split(b" ", 2)[1])
    finally:
        connection.close()


auth = "Authorization: Bearer " + token + "\r\nContent-Type: application/json\r\n"
assert raw(auth + "Content-Length: 2\r\nContent-Length: 2", b"{}") == 400
checks.append("duplicate_content_length_400")
assert raw(auth + "Transfer-Encoding: chunked\r\nContent-Length: 2", b"{}") == 400
checks.append("transfer_encoding_400")
assert raw(auth + "Expect: 100-continue\r\nContent-Length: 2", b"{}") == 400
checks.append("expect_continue_400")
assert raw(auth + "Authorization: Bearer " + token + "\r\nContent-Length: 2", b"{}") == 401
checks.append("duplicate_authorization_401")
assert raw(auth + "Content-Length: 1", b"{") == 400
checks.append("malformed_json_400")
assert raw("Authorization: Bearer wrong") == 401
checks.append("authentication_precedes_body_framing")
assert raw(auth + "Content-Length: 100", b"{", delay=True) == 400
checks.append("absolute_input_deadline_5_seconds")
assert stat.S_IMODE(s.sandbox_broker_socket.stat().st_mode) == 0o600
assert stat.S_IMODE(s.sandbox_broker_socket.parent.stat().st_mode) == 0o700
checks.append("private_socket_and_directory_modes")

with tempfile.TemporaryDirectory(prefix="broker-link-probe-") as name:
    root = Path(name)
    owned, foreign = root / "owned", root / "foreign"
    owned.mkdir()
    foreign.mkdir()
    (owned / "outside").symlink_to(foreign, target_is_directory=True)
    (owned / "inside").symlink_to(owned, target_is_directory=True)
    executor = MappedSandboxExecutor(s.resolution_sandbox_image, owned, Path("/approved/volume"))
    for candidate in (owned / "outside/source-0", owned / "inside/source-0"):
        try:
            executor.daemon_path(candidate)
        except WorkspaceError:
            pass
        else:
            raise AssertionError("Linked input unexpectedly accepted")
checks.append("actual_symlink_outside_and_inside_root_denied")

from repopilot.agent.tools import RunScope
from repopilot.resolution.broker_client import BrokerClient
from repopilot.resolution.profiles import GOLDEN_ROOT, load_profile
from repopilot.resolution.workspace import SavedSource, Workspace, digest

saved = []
for path in (GOLDEN_ROOT / "repository").iterdir():
    text = path.read_text()
    saved.append(SavedSource(path.name, text, digest(text), len(text.encode())))
with Workspace(RunScope(1, 1), saved) as workspace:
    client = BrokerClient(s.resolution_sandbox_image, workspace.root / "absent.sock", s.sandbox_broker_token_file)
    unavailable = client.run(workspace, load_profile("fee-days"))
    assert unavailable.infrastructure_error and not unavailable.passed
    workspace.verify()
checks.append("unavailable_broker_fails_closed_without_host_executor")
print(json.dumps({"mode": "real Linux API-container Unix/socket/path probe", "checks": checks}, indent=2))
