"""One bounded exact-context patch interface, with atomic revision publication."""

import difflib
from collections.abc import Mapping
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator

from repopilot.resolution.workspace import Workspace, WorkspaceError, digest, safe_path


class PatchError(ValueError):
    pass


class Edit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str = Field(min_length=1, max_length=240)
    old_text: str = Field(min_length=1, max_length=16_000)
    new_text: str = Field(max_length=16_000)

    _path = field_validator("path")(safe_path)


class PatchArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0, le=20)
    edits: list[Edit] = Field(min_length=1, max_length=6)


class ChangedFile(BaseModel):
    path: str
    original: str
    modified: str


class PatchRecord(BaseModel):
    attempt: int
    base_revision: int
    revision: int
    changed_paths: list[str]
    before_hashes: dict[str, str]
    after_hashes: dict[str, str]


def edit_permitted(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (
        path.endswith(".py")
        and not any(
            p.lower() in {"test", "tests", "validation", "config", "configs"}
            for p in parts
        )
        and not parts[-1]
        .lower()
        .startswith(("test_", "conftest", "setup", "config", "settings"))
        and not parts[-1].lower().endswith("_test.py")
    )


def changed_files(workspace: Workspace) -> list[ChangedFile]:
    return [
        ChangedFile(path=path, original=workspace.baseline[path], modified=content)
        for path, content in sorted(workspace.sources().items())
        if content != workspace.baseline[path]
    ]


def actual_diff(workspace: Workspace) -> str:
    return source_diff(workspace.baseline, workspace.sources())


def source_diff(before: Mapping[str, str], after: Mapping[str, str]) -> str:
    result: list[str] = []
    for path, content in sorted(after.items()):
        original = before[path]
        if original == content:
            continue
        for line in difflib.unified_diff(
            original.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        ):
            result.append(
                line
                if line.endswith("\n")
                else line + "\n\\ No newline at end of file\n"
            )
    return "".join(result)


class PatchEngine:
    def __init__(self, workspace: Workspace, editable_paths: frozenset[str]) -> None:
        self.workspace = workspace
        self.editable_paths = editable_paths
        self.records: list[PatchRecord] = []

    def apply(self, args: PatchArguments, *, attempt: int) -> PatchRecord:
        if args.expected_revision != self.workspace.revision:
            raise PatchError("Expected workspace revision does not match")
        if sum(len(e.old_text) + len(e.new_text) for e in args.edits) > 32_000:
            raise PatchError("Patch exceeds its text budget")
        before = self.workspace.sources()
        after = dict(before)
        for edit in args.edits:
            if edit.path not in self.editable_paths or not edit_permitted(edit.path):
                raise PatchError("File is outside the server edit allowlist")
            if edit.path not in after or after[edit.path].count(edit.old_text) != 1:
                raise PatchError("Patch context must match exactly once")
            if edit.old_text == edit.new_text:
                raise PatchError("Patch must change source")
            after[edit.path] = after[edit.path].replace(edit.old_text, edit.new_text, 1)
        if after == before:
            raise PatchError("Patch has no net effect")
        diff = source_diff(self.workspace.baseline, after)
        changed_size = sum(
            len(self.workspace.baseline[p]) + len(c)
            for p, c in after.items()
            if c != self.workspace.baseline[p]
        )
        if len(diff) > 40_000 or changed_size > 40_000:
            raise PatchError("Cumulative patch evidence exceeds its bound")
        paths = sorted(p for p in before if before[p] != after[p])
        record = PatchRecord(
            attempt=attempt,
            base_revision=self.workspace.revision,
            revision=self.workspace.revision + 1,
            changed_paths=paths,
            before_hashes={p: digest(before[p]) for p in paths},
            after_hashes={p: digest(after[p]) for p in paths},
        )
        try:
            self.workspace.publish(after, args.expected_revision)
        except WorkspaceError as exc:
            raise PatchError(str(exc)) from exc
        self.records.append(record)
        return record
