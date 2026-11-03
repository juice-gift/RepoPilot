"""Broker-owned materialization and execution. No network or caller-selected paths."""

import hashlib
import json
import os
import threading
from collections.abc import Callable
from pathlib import Path

from repopilot.agent.tools import RunScope
from repopilot.resolution.broker_protocol import BrokerRequest, validated_revisions
from repopilot.resolution.profiles import TestProfile
from repopilot.resolution.sandbox import SandboxExecutor, TestResult
from repopilot.resolution.workspace import (
    SavedSource,
    Workspace,
    WorkspaceError,
    digest,
    source_identity,
)


class BrokerBusy(RuntimeError):
    pass


class BrokerConflict(RuntimeError):
    pass


def sync_directory(path: Path) -> None:
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


class MappedSandboxExecutor(SandboxExecutor):
    """Mapping is established by trusted startup volume inspection, never HTTP."""

    def __init__(self, image_id: str, local_root: Path, daemon_root: Path) -> None:
        super().__init__(image_id)
        self.local_root, self.daemon_root = local_root.resolve(), daemon_root

    def daemon_path(self, path: Path) -> Path:
        if not path.resolve().is_relative_to(self.local_root):
            raise WorkspaceError("Broker input lies outside its owned data volume")
        if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
            raise WorkspaceError("Broker input links are forbidden")
        return self.daemon_root / path.relative_to(self.local_root)

    def _create_arguments(self, name: str, source: Path, validation: Path) -> list[str]:
        return super()._create_arguments(
            name, self.daemon_path(source), self.daemon_path(validation)
        )

    def _verify_container(self, data: dict, source: Path, validation: Path) -> None:
        super()._verify_container(
            data, self.daemon_path(source), self.daemon_path(validation)
        )


class BrokerRuntime:
    def __init__(
        self,
        *,
        load_profile: Callable[[str], TestProfile],
        executor_factory: Callable[[TestProfile], SandboxExecutor],
        ledger: Path,
        capacity: int = 512,
    ) -> None:
        if not 1 <= capacity <= 4096:
            raise ValueError("Invalid broker ledger capacity")
        self.load_profile, self.executor_factory = load_profile, executor_factory
        self.ledger, self.capacity = ledger, capacity
        if any(p.is_symlink() or p.is_junction() for p in (ledger, *ledger.parents)):
            raise WorkspaceError("Broker ledger links are forbidden")
        ledger.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.admission = threading.Lock()

    def run(self, request: BrokerRequest) -> TestResult:
        if not self.admission.acquire(blocking=False):
            raise BrokerBusy("Broker already has an active job")
        try:
            # Revalidate on every call, including replay; changed operator policy denies reuse.
            profile = self.load_profile(request.profile)
            states = validated_revisions(request, profile)
            executor = self.executor_factory(profile)
            request_hash = hashlib.sha256(
                request.model_dump_json().encode()
            ).hexdigest()
            ticket = self.ledger / (request.request_id + ".json")
            if ticket.is_symlink():
                raise WorkspaceError("Broker ledger entry is invalid")
            if ticket.exists():
                if ticket.stat().st_size > 32_000:
                    raise BrokerConflict("Broker ledger entry exceeds its bound")
                cached = json.loads(ticket.read_text(encoding="utf-8"))
                if (
                    cached.get("request_hash") != request_hash
                    or cached.get("state") != "complete"
                ):
                    raise BrokerConflict(
                        "Request identity conflicts or has an ambiguous prior outcome"
                    )
                result = TestResult.model_validate(cached["result"])
                if (
                    result.workspace_id != request.workspace_id
                    or result.revision != request.revision
                    or result.source_hash != source_identity(states[-1])
                    or result.image_id != executor.image_id
                    or result.profile_hash != profile.fingerprint()
                    or result.profile != profile.case_id
                ):
                    raise BrokerConflict("Cached test evidence identity mismatch")
                return result
            if sum(1 for _ in self.ledger.iterdir()) >= self.capacity:
                raise BrokerBusy("Broker request ledger requires operator maintenance")
            # Persist before any Docker effect. A crash marker is never blindly replayed.
            with ticket.open("x", encoding="utf-8") as handle:
                json.dump({"request_hash": request_hash, "state": "pending"}, handle)
                handle.flush()
                os.fsync(handle.fileno())
            sync_directory(self.ledger)
            saved = [
                SavedSource(p, text, digest(text), len(text.encode()))
                for p, text in request.baseline.items()
            ]
            with Workspace(RunScope(1, 1), saved) as workspace:
                owned_root = workspace.root
                for revision, state in enumerate(states[1:]):
                    workspace.publish(state, revision)
                result = executor.run(workspace, profile)
                if (
                    result.source_hash != source_identity(states[-1])
                    or result.revision != request.revision
                    or result.workspace_id != workspace.workspace_id
                    or result.image_id != executor.image_id
                    or result.profile != profile.case_id
                    or result.profile_hash != profile.fingerprint()
                ):
                    raise WorkspaceError("Broker tested source identity mismatch")
                result.workspace_id = request.workspace_id
            if owned_root.exists():
                result.cleanup_confirmed = False
                result.infrastructure_error = (
                    "Broker workspace cleanup could not be confirmed"
                )
            complete = {
                "request_hash": request_hash,
                "state": "complete",
                "result": result.model_dump(mode="json"),
            }
            temporary = ticket.with_suffix(".tmp")
            temporary.write_text(json.dumps(complete), encoding="utf-8")
            temporary.replace(ticket)
            sync_directory(self.ledger)
            return result
        finally:
            self.admission.release()
