# RepoPilot V4 implementation and acceptance status

**2026-10-22 — Incomplete: M1–M5 complete, M6 awaits external Qwen revalidation.**
This is a progress/acceptance report, not a declaration of V4 completion. The
[authorized goal](../goals/v4-issue-resolution-agent.md) remains active. Do not
start V5. Branch: `codex/v4-issue-resolution-agent`, baseline `d1ca767`.

## Implemented files and responsibilities

- `apps/api/src/repopilot/resolution/workspace.py`: persisted source integrity,
  private owned temporary directories, portable path/link/size checks, complete
  revision publication and lifecycle cleanup.
- `resolution/patch.py`: one strict exact-context editing interface, existing
  Python source allowlist, expected revision, atomic publication, actual unified
  diff, original/modified source and per-attempt hashes.
- `resolution/profiles.py` and `evaluation/resolution_golden/`: frozen source,
  independent tests, three issue contracts, edit permissions and manifest hash.
- `resolution/reads.py`: current modified list/read/search with revision identity.
- `resolution/sandbox.py` and `apps/api/sandbox/`: immutable prepared image,
  controlled Python/pytest execution, mandatory isolation inspection/preflight,
  bounded streams, test counts, timeout and forceful cleanup.
- `resolution/models.py`, `tools.py`, `runner.py`, `service.py`: typed plan/result,
  profile-scoped tools/permissions, explicit bounded repair loop and request
  cleanup. `agent/runner.py` only adds optional instruction accounting to its
  existing helper; V3 investigation behavior stays intact.
- `api/routes/resolution.py`, `main.py`, `config.py`, `.env.example`: separate thin
  resolve endpoint and immutable image setting. No schema or migration changes.
- `apps/web/src/api/resolution.ts`, `ResolutionResult.tsx`, `App.tsx`, `App.css`:
  typed/validated HTTP boundary, profile selection, original/modified source,
  plan, tests, patch, trace and actual verification status in the existing UI.
- Seven `tests/test_resolution_*.py` files cover workspace, patch, sandbox,
  runner, API, database integration and frozen evaluation; existing tests remain.
- `evaluation/resolution.py`: small explicit scripted/Qwen measurement CLI,
  complete result reports and exact-result review hashes. No V6 platform.
- README, this report, V4 goal/plan and JSON/PNG evidence document actual state.

## Architecture and data flow

```text
React selected Snapshot + profile + issue
→ POST /api/agent/resolve → strict request schema
→ verify saved Snapshot/file hashes + frozen approved profile
→ private OS temporary workspace outside RepoPilot (revision 0)
→ existing Responses provider.complete / V3 protocol safeguards
→ current source reads / baseline-only V1 retrieval and V2 symbols
→ public submit_plan → failing independent baseline
→ bounded apply_patch → complete new revision → actual diff
→ backend-selected Docker pytest profile at that revision
→ actual failure observation → optional repair/retest → typed result
→ remove container + temporary workspace → UI evidence
```

The model cannot choose host paths, run scope, image, shell command, test arguments,
security settings or permission expansion. A validated repair plan and failing
revision-0 baseline are required before edits. Invalid patch calls consume the
attempt budget. An unavailable capability is absent from the profile toolset.
Source/test observations are untrusted data; hidden reasoning is not recorded.

V1/V2 indexes remain unchanged baseline evidence after edits. Read current source
for modified behavior. Full V1 ingestion is not treated as a complete executable
environment: V4 executes only the frozen approved Golden profile. Original target
source and saved Snapshot are never modified by the product agent. The synchronous
API returns results without a persistent run/job subsystem or product-agent Git.

Defaults: 18 model turns, at most five calls per turn, four patch attempts, five
test executions, 180s wall-deadline admission, 90k core context/16k model output/
12k observation characters. API context/output use existing bounded settings.
SDK requests retain their 30s timeout/no retries. Late model responses cannot
authorize late tools. Docker preparation shares its execution deadline; forced
cleanup has separately bounded grace calls. Wall admission is not a guarantee of
instant cancellation of an already-running provider call. Browser disconnect does
not expose a new cancellation API; exception cancellation cleanup is tested.

## Dependencies and isolation evidence

No application dependency, migration, framework, service or lockfile was added.
The separate trusted test image uses pinned Python 3.13.13 base digest and pinned,
SHA256-verified pytest/iniconfig/packaging/pluggy/pygments wheels. Installation
occurs only during image preparation, never during agent test execution.

Real Linux Docker checks establish UID/GID 65534, zero effective/bounding
capabilities, NoNewPrivs=1, seccomp mode 2, read-only root/source/validation,
network and IPC disabled, one CPU, 256 MiB/no swap, 64 processes, 256 file
descriptors and 32 MiB noexec/nosuid/nodev tmpfs. Container inspection rejects
weakened settings before source import. No project/Docker-socket mount or app
credential injection is permitted. Only local npipe/unix engine endpoints run.

Actual independent tests exercise failed source/test/root writes, failed external
network connection, absent credentials/socket, process exhaustion, memory OOM,
output flooding/truncation, timeout container removal and cancellation cleanup.
Final container audit found no leftover resolution containers. On this Windows
host, `icacls` on an actual private workspace root showed only SYSTEM,
Administrators and OWNER RIGHTS full-control entries, with no broad Users/Everyone
access. Source/private workspace isolation is also covered against live PostgreSQL.

The controls follow the relevant
[Docker runtime options](https://docs.docker.com/engine/containers/run/) and
[default seccomp behavior](https://docs.docker.com/engine/security/seccomp/).
Docker shares a kernel/VM boundary and is not absolute isolation against malicious
code. The product intentionally supports controlled fixtures rather than arbitrary
repositories. Independent tests are bounded behavioral evidence; Python code could
deliberately tamper with a same-process test framework, so inspect the actual diff.

## Actual repair evaluation

Source/independent tests were frozen before model measurement; the canonical
manifest hash is `b0b4d6b0741f9c3d7829205d1b419efa2be2d2d909e2e29391e93e8d02d6ff0d`.
Expected behavior was not changed to make the reports pass.

| Measurement | Fee-days | Cross-file preconditions | Ambiguous cap |
| --- | --- | --- | --- |
| Scripted + real DB/Docker | Verified after deliberate failed patch/repair | Verified | Owner-decision plan, no changes |
| First full Qwen evaluation | Verified, 8 model calls/1 patch | Verified, 12 calls/1 patch | Safe zero-change stop, sandbox_failure; criterion failed |
| Corrected capability targeted Qwen trial | Not rerun | Not rerun | Provider failure at request 1; unverified |
| Independent targeted retry | Not rerun | Not rerun | Provider failure at request 1; unverified |

Fees baseline: 4 failing/4 passing tests; repaired revision: 8 passing tests.
Dispatch baseline: 2 failing/9 passing; repaired revision: 11 passing. The actual
Qwen fee patch removes the erroneous day offset while retaining cap/rounding and
guards. Its dispatch patch moves authentication before policy evaluation and
negative-attempt validation before permanent-job rejection, preserving the cap.
Original source/Snapshot and independent tests remain unchanged in these runs.

Reports: [scripted](v4-resolution-scripted-report.json),
[full Qwen](v4-resolution-qwen-report.json),
[targeted trial](v4-resolution-qwen-ambiguity-trial.json),
[targeted retry](v4-resolution-qwen-ambiguity-retry-report.json),
[exact-result reviews](v4-resolution-qwen-reviews.json).
Reviews are Codex source/diff/claim checks, not independent human review. Five
review hashes were recomputed and matched their exact saved results. Two positive
Qwen repairs are real external-model results; scripted protocols are not.

Keep two measured limitations visible:

1. The [initial browser run](v4-browser-initial-failure.md) repeatedly emitted
   invalid nested edit arguments and stopped after 18 turns with no changes.
   Explicit edit properties and precise safe validation feedback fixed the
   observed schema problem without relaxing permissions. The browser rerun made
   one actual patch, passed 8 tests at revision 1, and cleaned its workspace
   (10 calls, 44,877ms). Its prose incorrectly described 1% of $100 as one cent.
2. The first full Qwen negative case tried a test tool for a non-executable issue
   profile. It made no changes, but did not make the required owner decision.
   Profile-scoped capability advertisement is now corrected and deterministically
   tested; the real-model correction remains unverified because quota ran out.

These tiny, non-repeated runs do not establish generalized agent accuracy or a
causal success-rate improvement. Browser evidence:

![Verified browser fee repair](v4-browser-verified.png)

## Validation actually run

| Check | Result |
| --- | --- |
| Final ordinary `uv run pytest -q` | 238 passed / 24 opt-in DB/Docker skips |
| Final `RUN_DATABASE_TESTS=1 RUN_SANDBOX_TESTS=1 uv run pytest -q` | 262 passed, no skips |
| Focused live DB/Docker/actual HTTP route after final assertion strengthening | 2 passed; scripted owner-decision lifecycle, original/Snapshot isolation and cleanup verified |
| `uv run ruff check src tests migrations` | Passed |
| `uv run alembic current` / `check` | `0005_structural_index (head)` / no pending operations |
| Disposable clean migration replay | Passed in full live suite |
| `npm run build` | TypeScript and Vite production build passed |
| Real browser/API workflow | Positive Qwen patch, plan/tests/trace/source comparison and cleanup verified |
| V1 vector/hybrid CLIs | Baseline metrics unchanged |
| V2 structural CLI | Definitions 16/16, imports 5/5, targets 8/8, occurrences/status 21/21; seven queries unchanged |
| V3 scripted investigation CLI and existing regression tests | Three completed cases, all expected evidence found; investigation API preserved |
| Sandbox build and actual isolation tests | Passed; immutable image ID recorded in evaluation reports |
| Corrected negative Qwen revalidation | **Not passed: HTTP 403 free quota exhausted** |

V1 vector Hit@1/3/5: 0.75/0.875/1.0; MRR@5: 0.8375. Hybrid metrics remain 1.0.
Evidence is saved in `v4-v1-*-regression.json`, `v4-v2-structural-regression.json`
and `v4-v3-scripted-regression.json`. The existing AnyIO/Starlette deprecation
warning remains. Failed initial commands/runs and subsequent corrections remain
recorded in the plan; failed commands were not counted as passes.

## Acceptance and scope audit

| Goal requirements | Current evidence/status |
| --- | --- |
| Workspace identity, verified immutable source, path/byte limits, private lifecycle | Implemented; unit + live Snapshot tests + ACL inspection |
| Atomic bounded patch, revision guard, current reads, actual diff/provenance | Implemented; patch/unit/live integration and actual Qwen diffs |
| Mandatory Docker restrictions, no fallback/credentials/arbitrary selection, force cleanup | Implemented; actual security tests and image/runtime inspections |
| Structured plan, observe failure/repair/retest, execution/output budgets and safe failures | Implemented; deterministic + actual DB/Docker repair loop |
| Separate typed API/minimal UI, plan/patch/tests/status/trace/diagnostics | Implemented; API tests, build and actual browser evidence |
| At least one actual external-model independently verified repair | Achieved: both positive Qwen issues, plus browser fee repair |
| Frozen negative criterion, no unsupported modifications | Scripted passes; first real model safely stops but criterion fails; corrected real model unverified |
| V1–V3 regressions, migrations, lint/build | Passed as listed above |
| Documentation and completion boundary | Actual incomplete status documented; **full V4 completion not claimed** |

No V5 GitHub/MCP, V6 evaluation platform, V7 production architecture, arbitrary
shell interface, arbitrary repository execution, external dependency installation,
new state manager/UI framework, queues/workers/auth, speculative indexing or
multi-agent functionality was introduced. Git operations are engineering commits,
not capabilities exposed to the product agent.

## Git and remaining work

- `11d38c9` authorized V4 goal/preflight
- `7dc47e7` owned workspaces and frozen fixtures
- `8f933cf` atomic patch/current reads
- `77f6a2c` restricted Docker tests
- `69a9acc` planned bounded repair loop
- `46a261e` explicit edit schemas and actionable validation feedback
- `dec07c1` resolve API and React workflow
- `717ede1` frozen scripted/Qwen evaluation entry point
- `5a3c585` profile-scoped capabilities and owned validation cleanup

The final evidence/status documentation and live HTTP assertion strengthening are
committed separately. No push or destructive history change was performed.

The current blocker is confirmed by a safe provider diagnostic: HTTP 403,
`PERMISSION_DENIED`, free quota exhausted. Replenishing quota or changing the
provider's billing/free-tier-only policy requires the owner; it is outside this
engineering goal. No model switch or weakening of the frozen criterion is used
to conceal the failed check.

After Qwen capacity is restored, run from `apps/api` with `PYTHONPATH=src` and the
prepared immutable `RESOLUTION_SANDBOX_IMAGE`:

```powershell
uv run python -m repopilot.evaluation.resolution --mode qwen --case ambiguous-cap --output ../../docs/evaluation/v4-resolution-qwen-ambiguity-resumed.json
```

Review the exact result/diff/trace against the frozen safe decision criterion,
record its hash-bound verdict, then recheck any changed code and finish the V4
acceptance/completion report. Stop at V4/V5 only after that final acceptance.
