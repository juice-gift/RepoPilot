"""No fixture code is executed on the host. Docker tests are added separately."""

from pathlib import Path

import pytest

from repopilot.agent.tools import RunScope
from repopilot.resolution.profiles import GOLDEN_ROOT, load_profile
from repopilot.resolution.workspace import (
    MAX_FILES,
    SavedSource,
    Workspace,
    WorkspaceError,
    digest,
    safe_path,
)


def saved(path: str = "app.py", content: str = "value = 1\n") -> SavedSource:
    return SavedSource(path, content, digest(content), len(content.encode("utf-8")))


def golden_files() -> tuple[SavedSource, ...]:
    return tuple(
        saved(p.name, p.read_text(encoding="utf-8"))
        for p in sorted((GOLDEN_ROOT / "repository").iterdir())
    )


def test_owned_lifecycle_and_independent_identity():
    with (
        Workspace(RunScope(1, 2), [saved()]) as first,
        Workspace(RunScope(1, 2), [saved()]) as second,
    ):
        assert first.workspace_id != second.workspace_id
        assert first.root != second.root
        assert first.scope == RunScope(1, 2)
        assert first.revision == 0 and first.read("app.py") == "value = 1\n"
        root = first.root
        first.close()
        assert not root.exists()
        with pytest.raises(WorkspaceError):
            first.read("app.py")
        assert second.read("app.py") == "value = 1\n"


def test_cleanup_after_exception():
    with pytest.raises(RuntimeError), Workspace(RunScope(1, 1), [saved()]) as workspace:
        root = workspace.root
        raise RuntimeError("cancelled")
    assert not root.exists()


@pytest.mark.parametrize(
    "path",
    [
        "../x.py",
        "/x.py",
        "C:/x.py",
        "a\\x.py",
        "a//x.py",
        ".env",
        "secrets.py",
        "a/../x.py",
        "CON.py",
        "a./x.py",
        "a\n.py",
        "secret.key",
        ".git/x.py",
        "x.txt",
    ],
)
def test_reject_unsafe_paths(path):
    with pytest.raises(ValueError):
        safe_path(path)


def test_integrity_limits_and_collisions():
    with pytest.raises(WorkspaceError):
        Workspace(RunScope(1, 1), [SavedSource("a.py", "changed", "bad", 7)])
    with pytest.raises(WorkspaceError):
        Workspace(RunScope(1, 1), [saved("A.py"), saved("a.py")])
    with pytest.raises(WorkspaceError):
        Workspace(RunScope(1, 1), [saved("a.py"), saved("a.py/x.py")])
    with pytest.raises(WorkspaceError):
        Workspace(RunScope(1, 1), [saved(f"x{i}.py") for i in range(MAX_FILES + 1)])
    with pytest.raises(WorkspaceError):
        Workspace(RunScope(1, 1), [saved(content="x" * 1_000_001)])


def test_out_of_band_changes_rejected():
    with Workspace(RunScope(1, 1), [saved()]) as workspace:
        (workspace.source_dir / "app.py").write_text("tampered", encoding="utf-8")
        with pytest.raises(WorkspaceError):
            workspace.read("app.py")


def test_symlink_escape_rejected(tmp_path: Path):
    outside = tmp_path / "outside.py"
    outside.write_text("outside", encoding="utf-8")
    with Workspace(RunScope(1, 1), [saved()]) as workspace:
        path = workspace.source_dir / "app.py"
        path.unlink()
        try:
            path.symlink_to(outside)
        except OSError:
            # Windows unprivileged hosts: use a directory junction instead.
            import subprocess

            directory = path.parent / "escape"
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(directory), str(tmp_path)],
                capture_output=True,
                check=False,
            )
            assert result.returncode == 0
        with pytest.raises(WorkspaceError):
            workspace.read("app.py")
    assert outside.read_text(encoding="utf-8") == "outside"


def test_frozen_profiles_match_saved_source_and_deny_unapproved_snapshot():
    for case in ("fee-days", "dispatch-preconditions", "ambiguous-cap"):
        profile = load_profile(case)
        with Workspace(RunScope(1, 1), golden_files()) as workspace:
            profile.require_snapshot(workspace.sources())
        with pytest.raises(WorkspaceError):
            profile.require_snapshot({"other.py": "pass"})
    negative = load_profile("ambiguous-cap")
    assert (
        not negative.editable_paths
        and negative.expected_decision == "needs_owner_decision"
    )
    assert load_profile("dispatch-preconditions").editable_paths == {
        "policy.py",
        "workflow.py",
    }
    with pytest.raises(WorkspaceError):
        load_profile("../../shell")
