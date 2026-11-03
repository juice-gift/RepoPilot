"""Backend-owned frozen execution profiles. Model arguments cannot expand scope."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from repopilot.config import REPOSITORY_ROOT
from repopilot.resolution.workspace import WorkspaceError, digest, safe_path

GOLDEN_ROOT = REPOSITORY_ROOT / "apps/api/evaluation/resolution_golden"
FROZEN_MANIFEST_HASH = (
    "b0b4d6b0741f9c3d7829205d1b419efa2be2d2d909e2e29391e93e8d02d6ff0d"
)


@dataclass(frozen=True)
class TestProfile:
    __test__ = False
    case_id: str
    issue: str
    editable_paths: frozenset[str]
    validation: Mapping[str, bytes]
    expected_sources: Mapping[str, str]
    expected_decision: str
    baseline_failures: int
    expected_tests: int
    repository: str | None = None
    commit_sha: str | None = None
    image_id: str | None = None
    import_root: str = "."
    source_evidence_limit: int = 40_000

    def fingerprint(self) -> str:
        data = {
            "id": self.case_id,
            "issue": self.issue,
            "sources": dict(self.expected_sources),
            "editable": sorted(self.editable_paths),
            "validation": {
                p: hashlib.sha256(b).hexdigest() for p, b in self.validation.items()
            },
            "repository": self.repository,
            "commit": self.commit_sha,
            "image": self.image_id,
            "import_root": self.import_root,
            "expected_tests": self.expected_tests,
            "baseline_failures": self.baseline_failures,
            "source_evidence_limit": self.source_evidence_limit,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def require_snapshot(self, sources: Mapping[str, str]) -> None:
        if {path: digest(content) for path, content in sources.items()} != dict(
            self.expected_sources
        ):
            raise WorkspaceError(
                "Snapshot does not match the approved execution profile"
            )


def load_profile(
    case_id: str,
    *,
    registry_path: Path | None = None,
    registry_digest: str | None = None,
) -> TestProfile:
    if case_id.startswith("trusted-"):
        from repopilot.resolution.trusted_profiles import load_trusted_profile

        return load_trusted_profile(case_id, registry_path, registry_digest)
    # No paths, images, commands or test arguments are taken from a caller/model.
    manifest = json.loads((GOLDEN_ROOT / "manifest.json").read_text(encoding="utf-8"))
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != FROZEN_MANIFEST_HASH:
        raise WorkspaceError("Frozen profile manifest was changed")
    cases = {case["id"]: case for case in manifest["cases"]}
    if case_id not in cases:
        raise WorkspaceError("Unknown approved issue profile")
    case = cases[case_id]
    for relative, expected in manifest["files"].items():
        safe_path(relative)
        path = GOLDEN_ROOT / relative
        if path.is_symlink() or any(
            p.is_symlink() or p.is_junction()
            for p in path.parents
            if p.is_relative_to(GOLDEN_ROOT)
        ):
            raise WorkspaceError("Golden fixture links are forbidden")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise WorkspaceError("Frozen Golden fixture integrity mismatch")
    validation = {
        name: (GOLDEN_ROOT / "validation" / name).read_bytes()
        for name in case["validation_files"]
    }
    expected_sources = {
        name.removeprefix("repository/"): value
        for name, value in manifest["files"].items()
        if name.startswith("repository/")
    }
    editable = frozenset(case["editable_paths"])
    if not editable <= expected_sources.keys() or any(
        not p.endswith(".py") for p in editable
    ):
        raise WorkspaceError("Invalid profile edit allowlist")
    return TestProfile(
        case_id,
        case["issue"],
        editable,
        MappingProxyType(validation),
        MappingProxyType(expected_sources),
        case["expected_decision"],
        case["baseline_failures"],
        case["expected_tests"],
    )
