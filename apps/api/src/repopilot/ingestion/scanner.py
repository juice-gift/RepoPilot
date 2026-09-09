from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

MAX_FILE_BYTES = 1_000_000

SUPPORTED_LANGUAGES = {
    ".js": "javascript",
    ".jsx": "jsx",
    ".md": "markdown",
    ".markdown": "markdown",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
}

EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".next",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "out",
        "target",
        "venv",
    }
)

SENSITIVE_SUFFIXES = frozenset({".key", ".p12", ".pem", ".pfx"})
SENSITIVE_STEMS = frozenset(
    {"credential", "credentials", "id_ed25519", "id_rsa", "secret", "secrets"}
)


class RepositoryPathError(ValueError):
    pass


class NoSupportedFilesError(ValueError):
    pass


@dataclass(frozen=True)
class ScannedFile:
    path: str
    language: str
    content: str
    content_hash: str
    byte_size: int


@dataclass(frozen=True)
class SkippedFile:
    path: str
    reason: str


@dataclass(frozen=True)
class ScanResult:
    repository_path: Path
    files: tuple[ScannedFile, ...]
    skipped_files: tuple[SkippedFile, ...]
    excluded_directories: tuple[str, ...]

    @property
    def total_bytes(self) -> int:
        return sum(file.byte_size for file in self.files)

    @property
    def skipped_reason_counts(self) -> dict[str, int]:
        return dict(Counter(item.reason for item in self.skipped_files))


def resolve_repository_path(requested_path: str, allowed_root: Path) -> Path:
    root = allowed_root.expanduser().resolve()
    candidate = Path(requested_path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()

    if not resolved.is_relative_to(root):
        raise RepositoryPathError("Repository path is outside REPOSITORY_ALLOWED_ROOT")
    if not resolved.is_dir():
        raise RepositoryPathError("Repository path does not exist or is not a directory")
    return resolved


def classify_file(relative_path: Path, byte_size: int) -> str | None:
    name = relative_path.name.lower()
    suffix = relative_path.suffix.lower()

    if name == ".env" or name.startswith(".env."):
        return "sensitive"
    if suffix in SENSITIVE_SUFFIXES or relative_path.stem.lower() in SENSITIVE_STEMS:
        return "sensitive"
    if ".min." in name or ".generated." in name or name.endswith("_pb2.py"):
        return "generated"
    if byte_size > MAX_FILE_BYTES:
        return "too_large"
    if suffix not in SUPPORTED_LANGUAGES:
        return "unsupported_language"
    return None


def scan_repository(requested_path: str, allowed_root: Path) -> ScanResult:
    repository_path = resolve_repository_path(requested_path, allowed_root)
    accepted: list[ScannedFile] = []
    skipped: list[SkippedFile] = []
    excluded_directories: list[str] = []

    for path in sorted(repository_path.rglob("*"), key=lambda item: item.as_posix()):
        relative_path = path.relative_to(repository_path)

        if any(part.lower() in EXCLUDED_DIRECTORIES for part in relative_path.parts):
            if path.is_dir() and path.name.lower() in EXCLUDED_DIRECTORIES:
                excluded_directories.append(relative_path.as_posix())
            continue
        if path.is_dir():
            continue

        relative_name = relative_path.as_posix()
        try:
            resolved_file = path.resolve(strict=True)
        except (OSError, RuntimeError):
            skipped.append(SkippedFile(relative_name, "unreadable"))
            continue
        if not resolved_file.is_relative_to(repository_path):
            skipped.append(SkippedFile(relative_name, "outside_repository"))
            continue

        try:
            byte_size = resolved_file.stat().st_size
        except OSError:
            skipped.append(SkippedFile(relative_name, "unreadable"))
            continue

        reason = classify_file(relative_path, byte_size)
        if reason is not None:
            skipped.append(SkippedFile(relative_name, reason))
            continue

        try:
            raw_content = resolved_file.read_bytes()
        except OSError:
            skipped.append(SkippedFile(relative_name, "unreadable"))
            continue
        if b"\x00" in raw_content:
            skipped.append(SkippedFile(relative_name, "binary"))
            continue
        try:
            content = raw_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            skipped.append(SkippedFile(relative_name, "non_utf8"))
            continue

        accepted.append(
            ScannedFile(
                path=relative_name,
                language=SUPPORTED_LANGUAGES[relative_path.suffix.lower()],
                content=content,
                content_hash=sha256(raw_content).hexdigest(),
                byte_size=byte_size,
            )
        )

    if not accepted:
        raise NoSupportedFilesError("Repository contains no supported, safe source files")

    return ScanResult(
        repository_path=repository_path,
        files=tuple(accepted),
        skipped_files=tuple(skipped),
        excluded_directories=tuple(sorted(excluded_directories)),
    )


def calculate_snapshot_hash(files: tuple[ScannedFile, ...]) -> str:
    digest = sha256()
    for file in files:
        digest.update(file.path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.content_hash.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()
