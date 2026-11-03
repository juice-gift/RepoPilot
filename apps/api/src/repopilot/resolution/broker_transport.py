"""Authenticated local Unix HTTP transport; no TCP listener or command API."""

import hmac
import http.client
import json
import re
import socket
import stat
import threading
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer, ThreadingMixIn

from pydantic import ValidationError

from repopilot.resolution.broker_protocol import (
    MAX_REQUEST_BYTES,
    MAX_RESPONSE_BYTES,
    BrokerRequest,
)
from repopilot.resolution.broker_runtime import (
    BrokerBusy,
    BrokerConflict,
    BrokerRuntime,
)
from repopilot.resolution.workspace import WorkspaceError


def read_token(path: Path) -> str:
    if (
        not path.is_absolute()
        or any(p.is_symlink() or p.is_junction() for p in (path, *path.parents))
        or not stat.S_ISREG(path.stat().st_mode)
        or path.stat().st_size > 66
    ):
        raise ValueError("Broker credential file is invalid")
    raw = path.read_text(encoding="ascii")
    if not re.fullmatch(r"[0-9a-f]{64}\n?", raw):
        raise ValueError("Broker credential format is invalid")
    return raw.strip()


class UnixConnection(http.client.HTTPConnection):
    def __init__(self, path: Path, *, timeout: float = 60) -> None:
        super().__init__("localhost", timeout=timeout)
        self.path = path

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect(str(self.path))
        except BaseException:
            self.sock.close()
            raise


class BrokerHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    server_version = "RepoPilotBroker"
    sys_version = ""

    def setup(self) -> None:
        self.request.settimeout(5)
        super().setup()
        # A socket's per-read timeout alone permits slow trickle requests forever.
        self.read_timer = threading.Timer(5, self.expire_read)
        self.read_timer.daemon = True
        self.read_timer.start()

    def expire_read(self) -> None:
        try:
            self.request.shutdown(socket.SHUT_RD)
        except OSError:
            pass

    def finish(self) -> None:
        self.read_timer.cancel()
        super().finish()

    def log_message(self, format: str, *args: object) -> None:
        # Never log headers, source bytes or authentication values.
        pass

    def respond(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        if len(body) > MAX_RESPONSE_BYTES:
            status, body = 500, b'{"error":"Broker response exceeded its bound"}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        server = self.server
        try:
            # Reject duplicate credentials and framing before reading any source bytes.
            credentials = self.headers.get_all("Authorization", [])
            if len(credentials) != 1 or not hmac.compare_digest(
                credentials[0], "Bearer " + server.token
            ):
                self.respond(401, {"error": "Broker authentication required"})
                return
            if self.path != "/v1/tests":
                self.respond(404, {"error": "Unknown broker operation"})
                return
            lengths = self.headers.get_all("Content-Length", [])
            if (
                self.headers.get_all("Transfer-Encoding")
                or len(lengths) != 1
                or not re.fullmatch(r"[0-9]{1,8}", lengths[0])
                or not 1 <= int(lengths[0]) <= MAX_REQUEST_BYTES
                or self.headers.get("Content-Type") != "application/json"
                or self.headers.get("Expect")
            ):
                self.respond(400, {"error": "Invalid bounded broker request framing"})
                return
            body = self.rfile.read(int(lengths[0]))
            if len(body) != int(lengths[0]):
                raise ValueError("Incomplete request")
            request = BrokerRequest.model_validate_json(body)
            self.read_timer.cancel()
            result = server.runtime.run(request)
            self.respond(200, result.model_dump(mode="json"))
        except BrokerBusy:
            self.respond(429, {"error": "Broker unavailable for concurrent work"})
        except BrokerConflict:
            self.respond(
                409, {"error": "Broker request identity requires operator review"}
            )
        except (ValidationError, WorkspaceError, ValueError, KeyError):
            self.respond(
                400, {"error": "Broker request or approved profile is invalid"}
            )
        except (OSError, TimeoutError):
            self.close_connection = True
        except Exception:  # noqa: BLE001 - sanitized service boundary; never disclose source/errors
            self.respond(500, {"error": "Broker execution failed closed"})


class BrokerServer(ThreadingMixIn, TCPServer):
    # Windows host Python need only import the client. Actual server runs on Linux.
    address_family = getattr(socket, "AF_UNIX", None)
    daemon_threads = False
    request_queue_size = 4

    def __init__(self, path: Path, token: str, runtime: BrokerRuntime) -> None:
        self.token, self.runtime = token, runtime
        self.connections = threading.BoundedSemaphore(4)
        super().__init__(str(path), BrokerHandler)
        path.chmod(0o600)

    def server_bind(self) -> None:
        self.socket.bind(self.server_address)

    def process_request(self, request: socket.socket, client_address: str) -> None:
        if not self.connections.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.connections.release()
            raise

    def process_request_thread(
        self, request: socket.socket, client_address: str
    ) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.connections.release()
