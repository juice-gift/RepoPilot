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
| M1 | Owned workspace lifecycle, executable Golden fixtures | Current |
| M2 | Atomic patch, workspace-aware reads, actual diff | Pending |
| M3 | Docker executor, controlled profiles, real isolation tests | Pending |
| M4 | Structured plan, bounded resolution/repair loop | Pending |
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

M0 complete. M1–M6 and all V4 acceptance evidence remain outstanding.
No new dependency or product capability yet. Maintain this plan at each milestone,
commit reviewable increments, and record actual failures without claiming success.
