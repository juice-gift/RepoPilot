"""Build reproducible reviewed policy from pinned source metadata; no source execution."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "apps/api/evaluation/trusted_python"


def main() -> None:
    image = subprocess.check_output([
        "docker", "image", "inspect", "repopilot-tests:pre-v8", "--format", "{{.Id}}",
    ], text=True, timeout=10).strip()
    profiles = []
    for name, edit, test, count, failures, description in [
        ("itsdangerous", "src/itsdangerous/timed.py", "test_future_timestamp.py", 8, 3,
         "GitHub issue pallets/itsdangerous#126: TimestampSigner accepts correctly signed timestamps from the future when max_age is supplied. Reject a negative age with SignatureExpired while preserving valid, expired, and unlimited-age behavior."),
        ("more-itertools", "more_itertools/more.py", "test_replace_empty.py", 9, 6,
         "GitHub issue more-itertools/more-itertools#1336: replace produces padding or replacement output for an empty iterable with window_size greater than one. Empty input must yield nothing for either predicate outcome; preserve genuine None values and normal replacement behavior."),
    ]:
        metadata = json.loads((DATA / name / "source.json").read_text(encoding="utf-8"))
        profiles.append({
            "id": "trusted-" + name, "repository": metadata["repository"],
            "commit_sha": metadata["commit"], "issue": description,
            "image_id": image, "import_root": "src" if name == "itsdangerous" else ".",
            "expected_sources": metadata["sources"], "editable_paths": [edit],
            "validation": {test: (DATA / name / test).read_text(encoding="utf-8")},
            "expected_tests": count, "baseline_failures": failures,
            "source_evidence_limit": 500_000 if name == "more-itertools" else 40_000,
        })
    path = DATA / "profiles.json"
    path.write_text(json.dumps({"version": 1, "profiles": profiles}, indent=2) + "\n", encoding="utf-8")
    import hashlib
    print(json.dumps({"registry_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "image_id": image}))


if __name__ == "__main__":
    main()
