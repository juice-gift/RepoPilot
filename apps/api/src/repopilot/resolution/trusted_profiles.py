"""Operator-owned offline Python test policy. Never loaded from Issue/model input."""

import hashlib
import re
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from repopilot.resolution.patch import edit_permitted
from repopilot.resolution.profiles import TestProfile
from repopilot.resolution.workspace import WorkspaceError, safe_path


class TrustedProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    id: str = Field(pattern=r"^trusted-[a-z0-9-]{1,48}$")
    repository: str = Field(pattern=r"^[A-Za-z0-9-]+/[A-Za-z0-9_.-]+$", max_length=140)
    commit_sha: str = Field(pattern=r"^[a-f0-9]{40}$")
    issue: str = Field(min_length=1, max_length=4000)
    image_id: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    import_root: Literal[".", "src"] = "."
    expected_sources: dict[str, str] = Field(min_length=1, max_length=100)
    editable_paths: list[str] = Field(min_length=1, max_length=6)
    validation: dict[str, str] = Field(min_length=1, max_length=16)
    expected_tests: int = Field(ge=1, le=1000)
    baseline_failures: int = Field(ge=1, le=1000)
    source_evidence_limit: int = Field(default=40_000, ge=40_000, le=1_000_000)
    issue_number: int | None = Field(default=None, ge=1)
    original_issue_body: str | None = Field(default=None, min_length=1, max_length=4000)
    baseline_tree_sha: str | None = Field(default=None, pattern=r"^[a-f0-9]{40}$")
    baseline_entries: dict[str, dict[str, str]] | None = Field(
        default=None, max_length=5000
    )

    @model_validator(mode="after")
    def bounded_python_policy(self) -> "TrustedProfile":
        if (self.issue_number is None) != (self.original_issue_body is None):
            raise ValueError("Issue identity and original body are required together")
        if (self.baseline_tree_sha is None) != (self.baseline_entries is None):
            raise ValueError("Complete baseline tree metadata is required together")
        if self.baseline_entries is not None:
            from repopilot.github.trees import nested_tree

            if nested_tree(self.baseline_entries) != self.baseline_tree_sha:
                raise ValueError("Baseline Git tree mismatch")
        for path, digest in self.expected_sources.items():
            safe_path(path)
            if not re.fullmatch(r"[a-f0-9]{64}", digest):
                raise ValueError("Invalid source digest")
        if len(set(self.editable_paths)) != len(self.editable_paths):
            raise ValueError("Duplicate edit path")
        for path in self.editable_paths:
            safe_path(path)
            if (
                path not in self.expected_sources
                or not edit_permitted(path)
                or any(
                    part.lower() in {"tests", "test", "conftest.py", "setup.py"}
                    for part in path.split("/")
                )
                or Path(path).name.startswith("test_")
            ):
                raise ValueError(
                    "Only approved Python implementation files may be edited"
                )
        for path, text in self.validation.items():
            if (
                not re.fullmatch(r"test_[a-z_]+\.py", path)
                or len(text.encode()) > 100_000
            ):
                raise ValueError("Invalid protected validation input")
        if self.baseline_failures > self.expected_tests:
            raise ValueError("Invalid baseline failure count")
        return self


class Registry(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1]
    profiles: list[TrustedProfile] = Field(min_length=1, max_length=16)


def load_trusted_profile(
    case_id: str,
    registry_path: Path | None,
    registry_digest: str | None,
) -> TestProfile:
    try:
        if (
            registry_path is None
            or registry_digest is None
            or not registry_path.is_absolute()
        ):
            raise ValueError("No explicit trusted registry configured")
        if any(
            p.is_symlink() or p.is_junction()
            for p in (registry_path, *registry_path.parents)
        ):
            raise ValueError("Linked policy paths are forbidden")
        if registry_path.stat().st_size > 2_000_000:
            raise ValueError("Policy file too large")
        raw = registry_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != registry_digest:
            raise ValueError("Approved policy digest changed")
        registry = Registry.model_validate_json(raw)
        profiles = {p.id: p for p in registry.profiles}
        if len(profiles) != len(registry.profiles):
            raise ValueError("Duplicate trusted profile identity")
        profile = profiles[case_id]
    except (OSError, ValueError, KeyError, ValidationError):
        raise WorkspaceError(
            "Trusted Python profile is unavailable or not approved"
        ) from None
    return TestProfile(
        profile.id,
        profile.issue,
        frozenset(profile.editable_paths),
        MappingProxyType({p: text.encode() for p, text in profile.validation.items()}),
        MappingProxyType(profile.expected_sources),
        "repair",
        profile.baseline_failures,
        profile.expected_tests,
        profile.repository.lower(),
        profile.commit_sha,
        profile.image_id,
        profile.import_root,
        profile.source_evidence_limit,
        profile.issue_number,
        profile.original_issue_body,
        profile.baseline_tree_sha,
        MappingProxyType(profile.baseline_entries)
        if profile.baseline_entries is not None
        else None,
    )
