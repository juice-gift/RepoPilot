# RepoPilot V4 Execution Plan

## Goal and boundary

Implement the approved [V4 goal](../goals/v4-issue-resolution-agent.md): issue →
investigation → validated plan → bounded patch → Docker tests → repair → verified
patch and evidence. Only private temporary workspaces may change. No arbitrary
execution, external dependency installation, GitHub, MCP, workers or multi-agent
systems. Stop at V4/V5.

## M0 preflight (2026-10-21)

- Read AGENTS, PROJECT, V3 goal/plan/completion, relevant implementation/history.
- Clean `main`, exact approved baseline `d1ca7678fa482c7accea8b55afad94394413316c`.
- Ordinary pytest: 180 passed / 16 opt-in DB skips; Ruff and web build passed.
- Initially blocked: Docker Desktop ingest socket startup crash and DB timeout.
  On recheck Desktop recovered externally; existing PostgreSQL container healthy.
- Full `RUN_DATABASE_TESTS=1 uv run pytest`: 196 passed, including live V1/V2/V3
  tools, API and disposable migration replay. Existing AnyIO warning only.
- Alembic current: `0005_structural_index (head)`; check: no pending operations.
- V1 vector/hybrid, V2 structural and V3 scripted evaluation CLIs passed. First
  invocation lacked PYTHONPATH; reran successfully with `PYTHONPATH=src`.
- Linux engine 29.7.2, builtin seccomp/cgroupns. Actual Python probe: UID 65534,
  zero CapEff/CapBnd, NoNewPrivs=1, Seccomp=2, memory.max=268435456, pids.max=64.
  Read-only root, network none, CPU quota and tmpfs flags accepted.
- Docker Hub returned 429; official-image AWS public mirror pull succeeded:
  `public.ecr.aws/docker/library/python@sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f`.
- No architecture conflict. Draft approval footer in attachment superseded by
  its explicit owner authorization. Historical V3 completion remains historical.

## Milestones

| Milestone | Deliverable | Status |
| --- | --- | --- |
| M0 | Preflight, approved goal, execution plan | Complete |
| M1 | Owned workspace lifecycle, executable Golden fixtures | Complete |
| M2 | Atomic patch, workspace-aware reads, actual diff | Complete |
| M3 | Docker executor, controlled profiles, real isolation tests | Complete |
| M4 | Structured plan, bounded resolution/repair loop | Current |
| M5 | Typed resolve API and minimal React workflow | Pending |
| M6 | Frozen real-model evaluation, regressions and final review | Pending |

## Implementation decisions

- Keep V3 contracts and investigation behavior stable. Reuse provider protocol
  and loop validation helpers; V4 patch/test observations have their own types.
- Only backend-approved Python fixtures/profiles can execute. Snapshot matching
  is based on frozen file hashes, not an arbitrary path or model-selected command.
- Materialize persisted source only; source snapshots are not complete runnable
  environments. Test harness/dependencies are controlled independently.
- Model edits only explicitly approved existing source files. Tests, configuration
  and evaluation ground truth remain outside edit permission.
- No host execution fallback. Docker is defense in depth, not an absolute boundary
  for malicious code. Use only local single-user controlled fixtures in V4.

## Validation and remaining work

- M1 (2026-10-22): 21 focused tests passed, including real PostgreSQL saved
  snapshot → workspace, changed original source isolation and corrupt-source
  rejection. Full Ruff passed after import/style corrections. Workspace checks
  identity/count/bytes, portable paths, links/junctions, source hashes and snapshot
  hash; temporary root is private and external to RepoPilot. Each published
  revision is a complete directory; cleanup covers ordinary and exceptional exits.
- Frozen v1 source/validation manifest has three issues, strict per-case edits,
  independent pytest ground truth and explicit ambiguous-case refusal criterion.
  No fixture code was executed on the host. Actual failing baseline execution and
  independent test verification are still required in M3's Docker runtime.
- V4 snapshots with BOM/normalization that cannot reproduce their original byte
  hashes fail closed rather than silently claiming a verified executable snapshot.

- M2: 31 focused tests passed against live PostgreSQL; full Ruff passed.
  One strict exact-context `apply_patch` schema supports bounded changes to
  allowlisted existing Python sources only. Tests/config/secrets remain denied.
  Atomic complete revisions, stale-base rejection, multi-file failure rollback,
  I/O publication failure, actual unified diff, original/modified text and per-
  attempt hashes are covered. Current list/read/search include workspace/revision;
  unchanged V1/V2 indexes will be labeled baseline-only at the V4 tool boundary.

- M3: pinned Python image + hash-locked pytest wheels built successfully. Eight
  actual Docker tests passed; combined M1–M3 suite 39 passed, full Ruff passed.
  Golden baselines actually fail (fees: 4 failed/4 passed; dispatch: 2 failed/9
  passed); reference patches then pass independent checks (8/11 respectively).
  Corrected the pre-measurement expected fee failure count from 5 to observed 4;
  frozen source and test expectations unchanged. No model repair measured yet.
- Actual isolation evidence: read-only source/validation/root writes fail,
  external socket connection fails, credentials/socket absent, UID/capability/
  seccomp/cgroup constraints checked before source imports. Process exhaustion and
  memory OOM limits exercised; output flood is drained/bounded; timeout/cancel
  force-clean the exact container; temporary workspace cleanup verified.
- Executor refuses missing/unsafe images, remote engines, unavailable Docker and
  weakened inspect settings; uses no host fallback. Docker operation preparation
  shares a deadline, with separately bounded forced-cleanup calls. Public Python
  GPG metadata is not an application secret. Detailed limits/setup are documented
  in `apps/api/sandbox/README.md`. Image-only pytest dependencies reuse the existing
  test framework; no application dependency or application containerization added.
- One initial PowerShell pytest glob was not expanded (no tests ran); corrected
  explicit file-list invocation passed. Do not count the failed command as a pass.

M4–M6 and the remaining V4 acceptance evidence are outstanding.
