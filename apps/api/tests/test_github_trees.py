import json

import pytest

from repopilot.config import REPOSITORY_ROOT
from repopilot.github.client import GitHubMCPError
from repopilot.github.trees import nested_tree, object_hash, replace_blobs


@pytest.mark.parametrize("name", ["itsdangerous", "more-itertools"])
def test_nested_repository_tree_matches_actual_immutable_git_commit(name):
    data = json.loads(
        (
            REPOSITORY_ROOT
            / "apps/api/evaluation/trusted_python"
            / name
            / "source.json"
        ).read_text(encoding="utf-8")
    )
    assert nested_tree(data["tree_entries"]) == data["tree_sha"]
    assert any("/" in path for path in data["tree_entries"])


def test_patching_nested_blob_preserves_other_objects_and_modes():
    original = {
        "a/b.py": {"sha": object_hash("blob", b"old"), "mode": "100755"},
        ".github/workflows/ci.yml": {"sha": "b" * 40, "mode": "100644"},
        "link": {"sha": "c" * 40, "mode": "120000"},
    }
    modified = replace_blobs(original, {"a/b.py": "new"})
    assert nested_tree(original) != nested_tree(modified)
    assert modified["a/b.py"]["mode"] == "100755"
    assert modified["link"] == original["link"]
    assert modified[".github/workflows/ci.yml"] == original[".github/workflows/ci.yml"]
    with pytest.raises(GitHubMCPError):
        replace_blobs(original, {"link": "unsafe"})


@pytest.mark.parametrize(
    "path,entry",
    [
        ("../x", {"sha": "a" * 40, "mode": "100644"}),
        ("/x", {"sha": "a" * 40, "mode": "100644"}),
        ("a\\x", {"sha": "a" * 40, "mode": "100644"}),
        ("x", {"sha": "a" * 40, "mode": "160000"}),
        ("x", {"sha": "not-sha", "mode": "100644"}),
    ],
)
def test_unsafe_tree_metadata_is_rejected(path, entry):
    with pytest.raises(GitHubMCPError):
        nested_tree({path: entry})
