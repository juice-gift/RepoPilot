"""Owned, revisioned source copies. Never read a repository working tree."""

import hashlib
import re
import shutil
import stat
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Self
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from repopilot.agent.tools import RunScope, validate_path
from repopilot.config import REPOSITORY_ROOT
from repopilot.db.models import SnapshotFile
from repopilot.ingestion.scanner import classify_file
from repopilot.intelligence.service import require_snapshot

MAX_FILES = 100
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 4_000_000


class WorkspaceError(ValueError):
    pass


def digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def safe_path(value: str) -> str:
    validate_path(value)
    for part in value.split("/"):
        if (
            not re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", part)
            or part.endswith((".", " "))
            or part.startswith(".")
            or part.split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(10)),
                *(f"LPT{i}" for i in range(10)),
            }
        ):
            raise WorkspaceError("Unsupported portable workspace path")
    if len(value) > 240 or classify_file(Path(value), 0) is not None:
        raise WorkspaceError("File is not permitted in a source workspace")
    return value


def validate_sources(sources: Mapping[str, str]) -> None:
    if not 1 <= len(sources) <= MAX_FILES:
        raise WorkspaceError("Workspace file count exceeds its bound")
    folded: set[str] = set()
    total = 0
    for path, content in sources.items():
        safe_path(path)
        if path.casefold() in folded or "\x00" in content:
            raise WorkspaceError("Duplicate portable path or binary source")
        folded.add(path.casefold())
        size = len(content.encode("utf-8"))
        if size > MAX_FILE_BYTES:
            raise WorkspaceError("Workspace file exceeds its byte bound")
        total += size
    if total > MAX_TOTAL_BYTES:
        raise WorkspaceError("Workspace exceeds its total byte bound")
    for path in folded:
        parts = path.split("/")
        if any("/".join(parts[:i]) in folded for i in range(1, len(parts))):
            raise WorkspaceError("File and directory path collision")


@dataclass(frozen=True)
class SavedSource:
    path: str
    content: str
    content_hash: str
    byte_size: int


def snapshot_sources(session: Session, scope: RunScope) -> tuple[SavedSource, ...]:
    snapshot = require_snapshot(session, scope.repository_id, scope.snapshot_id)
    if (
        snapshot.accepted_file_count > MAX_FILES
        or snapshot.total_bytes > MAX_TOTAL_BYTES
    ):
        raise WorkspaceError("Snapshot exceeds workspace limits")
    files = session.scalars(
        select(SnapshotFile)
        .where(SnapshotFile.snapshot_id == scope.snapshot_id)
        .order_by(SnapshotFile.path)
        .limit(MAX_FILES + 1)
    )
    # V1's identity uses Python path ordering, not database collation ordering.
    result = tuple(
        sorted(
            (
                SavedSource(f.path, f.content, f.content_hash, f.byte_size)
                for f in files
            ),
            key=lambda file: file.path,
        )
    )
    if (
        len(result) != snapshot.accepted_file_count
        or sum(f.byte_size for f in result) != snapshot.total_bytes
    ):
        raise WorkspaceError("Snapshot metadata does not match saved files")
    identity = hashlib.sha256()
    for file in result:
        identity.update(file.path.encode("utf-8") + b"\0")
        identity.update(file.content_hash.encode("ascii") + b"\0")
    if identity.hexdigest() != snapshot.content_hash:
        raise WorkspaceError("Snapshot identity does not match saved files")
    return result


class Workspace:
    """One owner, no source execution, only complete revisions become visible.

    Each revision is a fresh directory. A failed publish cannot affect the current
    revision. Docker later mounts that exact revision read-only. All directories
    live in a private OS temporary directory outside RepoPilot.
    """

    def __init__(self, scope: RunScope, files: Sequence[SavedSource]) -> None:
        sources: dict[str, str] = {}
        for file in files:
            if (
                file.path in sources
                or digest(file.content) != file.content_hash
                or len(file.content.encode("utf-8")) != file.byte_size
            ):
                raise WorkspaceError("Saved source integrity mismatch")
            sources[file.path] = file.content
        validate_sources(sources)
        self.scope = scope
        self.workspace_id = uuid4().hex
        self.revision = 0
        self._baseline = MappingProxyType(dict(sources))
        self._current = dict(sources)
        self._temporary = tempfile.TemporaryDirectory(prefix="repopilot-resolution-")
        self.root = Path(self._temporary.name).resolve()
        self._closed = False
        try:
            if self.root.is_relative_to(REPOSITORY_ROOT.resolve()):
                raise WorkspaceError("Workspace must be outside RepoPilot")
            # Python 3.13 handles 0700 with a user-only ACL on Windows too.
            self._source_dir = self._write_revision(sources, 0)
        except BaseException:
            self.close()
            raise

    @property
    def baseline(self) -> Mapping[str, str]:
        return self._baseline

    @property
    def source_dir(self) -> Path:
        self.verify()
        return self._source_dir

    def _write_revision(self, sources: Mapping[str, str], revision: int) -> Path:
        directory = self.root / f"source-{revision}"
        directory.mkdir(mode=0o755)
        try:
            for name, content in sources.items():
                path = directory / name
                path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                path.write_bytes(content.encode("utf-8"))
            return directory
        except BaseException:
            shutil.rmtree(directory)
            raise

    def verify(self) -> None:
        if (
            self._closed
            or self.root.is_symlink()
            or self.root.is_junction()
            or not self.root.is_dir()
        ):
            raise WorkspaceError("Workspace is closed or invalid")
        if (
            self._source_dir.is_symlink()
            or self._source_dir.is_junction()
            or not self._source_dir.is_dir()
        ):
            raise WorkspaceError("Source revision was replaced")
        found: set[str] = set()
        for path in self._source_dir.rglob("*"):
            mode = path.lstat().st_mode
            if (
                path.is_symlink()
                or path.is_junction()
                or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode))
            ):
                raise WorkspaceError("Links and special files are forbidden")
            if path.is_file():
                name = path.relative_to(self._source_dir).as_posix()
                if name not in self._current or path.stat().st_size > MAX_FILE_BYTES:
                    raise WorkspaceError("Unexpected workspace file")
                if path.read_bytes() != self._current[name].encode("utf-8"):
                    raise WorkspaceError("Workspace changed outside the patch engine")
                found.add(name)
        if found != self._current.keys():
            raise WorkspaceError("Workspace file disappeared")

    def sources(self) -> dict[str, str]:
        self.verify()
        return dict(self._current)

    def read(self, path: str) -> str:
        safe_path(path)
        self.verify()
        if path not in self._current:
            raise WorkspaceError("Workspace file not found")
        return self._current[path]

    def publish(self, sources: Mapping[str, str], expected_revision: int) -> None:
        """Only the patch engine supplies a validated complete new source map."""
        self.verify()
        if expected_revision != self.revision:
            raise WorkspaceError("Workspace revision mismatch")
        validate_sources(sources)
        if sources.keys() != self._current.keys():
            raise WorkspaceError("V4 permits updating existing files only")
        directory = self._write_revision(sources, self.revision + 1)
        self._current = dict(sources)
        self._source_dir = directory
        self.revision += 1

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._temporary.cleanup()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
