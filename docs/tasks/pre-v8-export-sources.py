"""Copy only reviewed Python package blobs from two pinned Git object databases.

No checkout, package installation, imports or third-party execution on the host.
"""

import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "apps/api/evaluation/trusted_python"
CASES = [
    ("itsdangerous", "pallets/itsdangerous", "1a9b8d1f9968eb248bda69f39d373a6330b692ba", "src/itsdangerous/", 126),
    ("more-itertools", "more-itertools/more-itertools", "v11.1.0", "more_itertools/", 1336),
]


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], timeout=30)


def main() -> None:
    observations = []
    for name, repository, revision, prefix, issue in CASES:
        repo = Path.home() / "AppData/Local/Temp" / ("repopilot-pre-v8-" + name)
        commit = git(repo, "rev-parse", revision + "^{commit}").decode().strip()
        entries = git(repo, "ls-tree", "-r", "--name-only", commit).decode().splitlines()
        sources = {}
        imports = set()
        for relative in entries:
            if not relative.startswith(prefix) or not relative.endswith(".py"):
                continue
            raw = git(repo, "show", f"{commit}:{relative}")
            text = raw.decode("utf-8")
            # Parse source as data only. Never import anything from the export.
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    imports.add(node.module or "")
            target = OUTPUT / name / "repository" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            sources[relative] = hashlib.sha256(raw).hexdigest()
        license_path = "LICENSE.rst" if name == "itsdangerous" else "LICENSE"
        (OUTPUT / name / "LICENSE.txt").write_bytes(git(repo, "show", f"{commit}:{license_path}"))
        metadata = {
            "repository": repository, "commit": commit, "issue_number": issue,
            "issue_url": f"https://github.com/{repository}/issues/{issue}",
            "projection": "Python package source only; not entire Git tree",
            "sources": sources, "absolute_imports": sorted(imports),
            "tree_sha": git(repo, "rev-parse", commit + "^{tree}").decode().strip(),
            "tree_entries": {},
        }
        for raw_entry in git(repo, "ls-tree", "-rz", commit).split(b"\0"):
            if not raw_entry:
                continue
            head, path = raw_entry.split(b"\t", 1)
            mode, kind, sha = head.decode().split()
            if kind != "blob":
                raise ValueError("Unsupported non-blob repository entry")
            metadata["tree_entries"][path.decode()] = {"mode": mode, "sha": sha}
        (OUTPUT / name / "source.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        observations.append({"repository": repository, "commit": commit, "files": len(sources), "imports": sorted(imports)})
    print(json.dumps(observations, indent=2))


if __name__ == "__main__":
    main()
