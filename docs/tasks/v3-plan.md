# RepoPilot V3 Execution Plan

## Goal and boundary

Implement the authorized [V3 goal](../goals/v3-repository-agent.md): an explicit,
bounded read-only repository investigation loop reusing persisted V1/V2 data.
No writes, execution, sandbox, GitHub, MCP, workers or multiple agents. Stop at V3/V4.

## Preflight (2026-10-14)

- Read AGENTS, PROJECT, V2 goal/plan/completion, actual implementation and history.
- Initial HEAD `858075e` is V2 completion; clean main checkout, no V3 implementation.
- Stage 0/V1/V2 implementations and frozen datasets exist and match the reports.
- Started the existing local database with `docker compose up -d database`.
- Ordinary tests: 112 passed / 14 skipped. Complete live suite: 126 passed,
  including disposable migration replay. Existing AnyIO warning only.
- Alembic current: `0005_structural_index (head)`; check: no pending operations.
- Ruff and frontend production build passed. No architecture conflict/blocker.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| M0 | Preflight, authorized goal, execution plan | Complete |
| M1 | Typed allowlist and bounded snapshot tools with tests | Current |
| M2 | Provider extension and explicit bounded loop/trace with deterministic tests | Pending |
| M3 | Thin investigate API and minimal existing-workflow React UI | Pending |
| M4 | Frozen multistep baseline, live integration/provider validation and regressions | Pending |
| Final | Acceptance/scope/security/Git audit and completion documentation | Pending |

## Decisions

- Snapshot scope is immutable server-owned run context, never model arguments.
- Tools read saved SnapshotFile, V2 navigation and V1 retrieve_evidence only.
  Indexing remains an explicit operation outside the agent; no schema change needed.
- Lexical baseline is literal substring search in PostgreSQL saved source with
  deterministic file/line ordering, bounded result count and source snippets.
- Tool results have typed evidence, JSON character limits, explicit truncation;
  runner bounds turns, calls per turn, model output and accumulated input.
- Extend existing Responses providers minimally. SDK objects remain in provider
  code; only text/call ID/name/argument strings cross the boundary. No reasoning
  content enters traces or replay. Use `store=false`, no previous_response_id.
- Unknown/invalid/failing calls return bounded safe observations; model can
  recover on the next turn. Failures and exhausted budgets have explicit reasons.
- Run state/trace is returned synchronously, not persisted as a new subsystem.
- Freeze small human-inspectable tasks before measurement. Scripted evaluation
  proves orchestration/evidence regressions; Qwen evaluation is reported separately.

## Validation and progress

See preflight above. M1–Final validation will be recorded as it is executed.
No new dependencies planned. No remaining preflight blocker.
