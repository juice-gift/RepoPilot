import pytest
from pydantic import ValidationError
from test_resolution_workspace import saved

from repopilot.agent.tools import ReadFileArguments, RunScope, SearchCodeArguments
from repopilot.resolution.patch import (
    PatchArguments,
    PatchEngine,
    PatchError,
    actual_diff,
    changed_files,
)
from repopilot.resolution.reads import WorkspaceReader
from repopilot.resolution.workspace import Workspace


def patch(revision=0, path="app.py", old="value = 1", new="value = 2"):
    return PatchArguments(
        expected_revision=revision,
        edits=[{"path": path, "old_text": old, "new_text": new}],
    )


def test_real_patch_diff_current_read_and_provenance():
    with Workspace(RunScope(1, 2), [saved()]) as workspace:
        engine = PatchEngine(workspace, frozenset({"app.py"}))
        first = engine.apply(patch(), attempt=1)
        assert first.before_hashes != first.after_hashes
        assert (first.base_revision, first.revision) == (0, 1)
        assert workspace.baseline["app.py"] == "value = 1\n"
        assert "-value = 1\n+value = 2\n" in actual_diff(workspace)
        assert changed_files(workspace)[0].modified == "value = 2\n"
        reader = WorkspaceReader(workspace)
        result = reader.read_file(ReadFileArguments(path="app.py"))
        assert result["revision"] == 1 and result["items"][0]["content"] == "value = 2"
        assert reader.search_code(SearchCodeArguments(query="value = 1"))["items"] == []
        engine.apply(patch(1, old="value = 2", new="value = 3"), attempt=2)
        assert len(engine.records) == 2
        assert "value = 3" in actual_diff(workspace)


def test_failed_multifile_patch_is_atomic_and_stale_revision_denied():
    with Workspace(RunScope(1, 2), [saved(), saved("b.py")]) as workspace:
        engine = PatchEngine(workspace, frozenset({"app.py", "b.py"}))
        args = patch()
        args.edits.append(patch(path="b.py", old="nonexistent").edits[0])
        with pytest.raises(PatchError, match="exactly once"):
            engine.apply(args, attempt=1)
        assert (
            workspace.revision == 0
            and actual_diff(workspace) == ""
            and not engine.records
        )
        engine.apply(patch(), attempt=2)
        with pytest.raises(PatchError, match="revision"):
            engine.apply(patch(), attempt=3)


def test_io_failure_rolls_back_entire_publication(monkeypatch):
    with Workspace(RunScope(1, 2), [saved()]) as workspace:
        engine = PatchEngine(workspace, frozenset({"app.py"}))
        directory = workspace.source_dir

        def failed(*args):
            raise OSError("disk full")

        monkeypatch.setattr(workspace, "_write_revision", failed)
        with pytest.raises(OSError):
            engine.apply(patch(), attempt=1)
        assert workspace.source_dir == directory and workspace.revision == 0
        assert workspace.read("app.py") == "value = 1\n" and not engine.records


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_app.py",
        "test_app.py",
        "config.py",
        "settings.py",
        "README.md",
        "new.py",
    ],
)
def test_permissions_protect_tests_config_and_unapproved_files(path):
    with Workspace(RunScope(1, 2), [saved(path)]) as workspace:
        editable = frozenset() if path == "new.py" else frozenset({path})
        with pytest.raises(PatchError, match="allowlist"):
            PatchEngine(workspace, editable).apply(patch(path=path), attempt=1)
        assert workspace.revision == 0


def test_patch_schema_and_ambiguous_context():
    with pytest.raises(ValidationError):
        PatchArguments.model_validate(
            {"expected_revision": 0, "edits": [], "shell": "whoami"}
        )
    with (
        Workspace(
            RunScope(1, 2), [saved(content="value = 1\nvalue = 1\n")]
        ) as workspace,
        pytest.raises(PatchError),
    ):
        PatchEngine(workspace, frozenset({"app.py"})).apply(patch(), attempt=1)
