"""API-side data client. Broker failure never falls back to local execution."""

import http.client
from pathlib import Path
from time import monotonic
from uuid import uuid4

from repopilot.config import Settings
from repopilot.resolution.broker_protocol import (
    MAX_REQUEST_BYTES,
    MAX_RESPONSE_BYTES,
    BrokerRequest,
)
from repopilot.resolution.broker_transport import UnixConnection, read_token
from repopilot.resolution.profiles import TestProfile
from repopilot.resolution.sandbox import SandboxError, SandboxExecutor, TestResult
from repopilot.resolution.workspace import Workspace, WorkspaceError, source_identity


class BrokerClient(SandboxExecutor):
    def __init__(self, image_id: str, socket_path: Path, token_file: Path) -> None:
        super().__init__(image_id)
        self.socket_path, self.token_file = socket_path, token_file

    def run(self, workspace: Workspace, profile: TestProfile) -> TestResult:
        started = monotonic()
        workspace.verify()
        expected_source = source_identity(workspace.sources())
        image_id = profile.image_id or self.image_id
        request = BrokerRequest(
            request_id=uuid4().hex,
            workspace_id=workspace.workspace_id,
            profile=profile.case_id,
            profile_hash=profile.fingerprint(),
            revision=workspace.revision,
            baseline=dict(workspace.baseline),
            updates=workspace.revision_updates(),
        )
        connection = UnixConnection(self.socket_path)
        try:
            body = request.model_dump_json().encode()
            if len(body) > MAX_REQUEST_BYTES:
                raise ValueError("Broker request exceeds its bound")
            if any(p.is_symlink() or p.is_junction() for p in self.socket_path.parents):
                raise WorkspaceError("Broker socket parent links are forbidden")
            connection.request(
                "POST",
                "/v1/tests",
                body,
                {
                    "Authorization": "Bearer " + read_token(self.token_file),
                    "Content-Type": "application/json",
                },
            )
            response = connection.getresponse()
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            if response.status != 200 or len(payload) > MAX_RESPONSE_BYTES:
                raise ValueError("Broker refused execution")
            result = TestResult.model_validate_json(payload)
            if (
                result.workspace_id != workspace.workspace_id
                or result.revision != workspace.revision
                or result.source_hash != expected_source
                or result.profile != profile.case_id
                or result.profile_hash != profile.fingerprint()
                or result.image_id != image_id
                or result.expected_tests != profile.expected_tests
                or result.command
                != ["python", "-I", "-B", "/opt/repopilot/run_tests.py"]
            ):
                raise WorkspaceError("Broker evidence identity mismatch")
            workspace.verify()
            return result
        except (OSError, ValueError, http.client.HTTPException):
            return TestResult(
                workspace_id=workspace.workspace_id,
                revision=workspace.revision,
                profile=profile.case_id,
                profile_hash=profile.fingerprint(),
                source_hash=expected_source,
                image_id=image_id,
                exit_code=None,
                stdout="",
                stderr="",
                elapsed_ms=round((monotonic() - started) * 1000, 3),
                infrastructure_error="Authenticated local Sandbox Broker unavailable or evidence invalid",
            )
        finally:
            connection.close()


def create_executor(settings: Settings) -> SandboxExecutor:
    if not settings.resolution_sandbox_image:
        raise SandboxError("An approved Sandbox image is required")
    if settings.sandbox_broker_socket is not None:
        return BrokerClient(
            settings.resolution_sandbox_image,
            settings.sandbox_broker_socket,
            settings.sandbox_broker_token_file,
        )
    return SandboxExecutor(settings.resolution_sandbox_image)
