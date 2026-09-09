from pathlib import Path

import pytest

from repopilot.ingestion.scanner import (
    MAX_FILE_BYTES,
    NoSupportedFilesError,
    RepositoryPathError,
    calculate_snapshot_hash,
    scan_repository,
)


def test_scan_repository_accepts_supported_languages_and_filters_unsafe_files(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "sample"
    repository.mkdir()
    (repository / "app.py").write_text("def hello():\n    return 'hello'\n", encoding="utf-8")
    (repository / "view.tsx").write_text("export const View = () => <div />;\n", encoding="utf-8")
    (repository / "README.md").write_text("# Sample\n", encoding="utf-8")
    (repository / ".env").write_text("TOKEN=not-indexed\n", encoding="utf-8")
    (repository / "private.pem").write_text("not-indexed\n", encoding="utf-8")
    (repository / "bundle.min.js").write_text("const x=1;", encoding="utf-8")
    (repository / "image.py").write_bytes(b"\x00\x01\x02")
    (repository / "notes.txt").write_text("unsupported", encoding="utf-8")
    (repository / "large.py").write_bytes(b"a" * (MAX_FILE_BYTES + 1))
    (repository / "node_modules").mkdir()
    (repository / "node_modules" / "ignored.js").write_text(
        "export const ignored = true;", encoding="utf-8"
    )

    result = scan_repository(str(repository), tmp_path)

    assert [(item.path, item.language) for item in result.files] == [
        ("README.md", "markdown"),
        ("app.py", "python"),
        ("view.tsx", "tsx"),
    ]
    assert result.skipped_reason_counts == {
        "generated": 1,
        "binary": 1,
        "too_large": 1,
        "unsupported_language": 1,
        "sensitive": 2,
    }
    assert result.excluded_directories == ("node_modules",)
    assert "TOKEN=not-indexed" not in "".join(item.content for item in result.files)


def test_scan_repository_rejects_paths_outside_allowed_root(tmp_path: Path) -> None:
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(RepositoryPathError, match="outside"):
        scan_repository(str(outside), allowed_root)


def test_scan_repository_rejects_repository_without_supported_files(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "empty"
    repository.mkdir()
    (repository / "data.csv").write_text("a,b\n", encoding="utf-8")

    with pytest.raises(NoSupportedFilesError, match="no supported"):
        scan_repository(str(repository), tmp_path)


def test_snapshot_hash_is_deterministic_and_changes_with_content(tmp_path: Path) -> None:
    repository = tmp_path / "sample"
    repository.mkdir()
    source = repository / "app.py"
    source.write_text("value = 1\n", encoding="utf-8")

    first = scan_repository(str(repository), tmp_path)
    repeated = scan_repository(str(repository), tmp_path)
    source.write_text("value = 2\n", encoding="utf-8")
    changed = scan_repository(str(repository), tmp_path)

    assert calculate_snapshot_hash(first.files) == calculate_snapshot_hash(
        repeated.files
    )
    assert calculate_snapshot_hash(first.files) != calculate_snapshot_hash(
        changed.files
    )
