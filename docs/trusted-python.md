# Approved Python execution profiles

Support is intentionally limited to explicitly reviewed pure-Python package-source
projections at immutable commits, with root or src layouts and independent pytest
validation. This does not execute arbitrary Python repositories, packaging hooks,
project pytest configuration, dependency installers, network services or shells.
Original working trees and stored snapshots remain immutable.

The operator policy is a JSON registry outside Issue/model control. Configure an
absolute `TRUSTED_PROFILE_REGISTRY` and its exact `TRUSTED_PROFILE_REGISTRY_SHA256`
together. No HTTP endpoint uploads or approves these files. The `trusted-*` profile
name alone grants no execution permission. Policy bytes, supported fields, source
hashes, commit, edit paths, independent test inputs, exact image ID, expected counts
and import root must validate before execution. No symlink/junction policy paths.
Changing the approved file without changing its configured hash fails closed.

The API contract keeps the same four request fields. Its `profile` permits frozen
IDs and bounded `trusted-*` IDs. The server selects the profile. Local trusted
resolution additionally requires the Snapshot commit and exact reviewed Issue
description. A Snapshot containing retrievable files is not automatically executable.
GitHub provenance/integration remains under active implementation; historical
bindings continue to use frozen policies until that work is validated.

Commands and container flags remain server-owned and fixed. Root/src import roots
are data for the trusted runner, not arbitrary PYTHONPATH or a shell command.
Runtime preparation uses only the existing hash-pinned pytest image. No repository
dependency installation occurs. A new image must be built/reviewed/pinned before
selecting it. Application containers still have no daemon capability.

Every actual test result records workspace/revision, policy fingerprint, image,
command, status, exit code, timeout, bounded diagnostics, runtime isolation and
cleanup. Policy fingerprints include source hashes, tests, image, issue, permissions
and evidence budget. Trusted profiles can select a bounded whole-source evidence
limit up to 1MB for real large modules; default stays 40KB and diff cap stays 40KB.
Host execution and unrestricted model container arguments remain forbidden.

Current reviewed corpus and actual results: [review](evaluation/pre-v8-python-review.md).
Source exports retain upstream licenses. Export/review policy scripts live under
docs/tasks for reproducibility. Rebuild policy image IDs only after reviewing the
same pinned recipe, then review the resulting exact registry hash. Do not treat
regeneration as an approval granted by Issue text.

From apps/api, actual regression:

```powershell
$env:RUN_TRUSTED_PYTHON_TESTS='1'
uv run pytest tests/test_trusted_profiles.py -q
```

This requires the approved `repopilot-tests:pre-v8` image identified in the corpus
registry. Without the explicit flag, live tests are skipped, not passed. Direct
baseline/patch evidence in docs/evaluation comes from real Docker but deterministic
patches, not a live model. Full pre-V8 acceptance remains in progress.
