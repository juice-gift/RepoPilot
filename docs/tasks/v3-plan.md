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
| M1 | Typed allowlist and bounded snapshot tools with tests | Complete |
| M2 | Provider extension and explicit bounded loop/trace with deterministic tests | Complete |
| M3 | Thin investigate API and minimal existing-workflow React UI | Complete |
| M4 | Frozen multistep baseline, live integration/provider validation and regressions | Complete |
| Final | Acceptance/scope/security/Git audit and completion documentation | Current |

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

- M1: 30 tool unit cases plus one live PostgreSQL full-tool/isolation test passed.
  Covers invalid typed arguments/path traversal/scope overrides, literal SQL
  wildcard escaping, saved-source reads despite working-tree changes, missing
  indexes, V1/V2 reuse and whole-JSON output bounding. Ruff passed after formatting.
  Scope review: queries only; no filesystem access, indexing or schema changes.
- M2: 60 focused tests passed (tools, loop, provider boundary, PostgreSQL and V1
  generation); full Ruff passed. Multi-turn/multi-call, recovery, unknown/invalid
  calls, infrastructure failures, context/schema accounting, max turns, duplicate
  IDs, incomplete/oversized output, citation identity and untrusted-data separation
  covered. Real DB scripted and local deterministic runs use saved snapshot source.
  Existing generate contract preserved; complete uses the same Responses clients.
- M3: ordinary suite 174 passed / 15 DB skips; Ruff and frontend build passed.
  Ten API cases cover validation, OpenAPI/typed result, missing resource/provider,
  database failure and inspectable provider-failure results. Browser path on
  temporary ports 8001/5174 passed: select persisted golden snapshot → investigate
  → two real tool calls → final answer → expanded read observation and saved source.
  Temporary test origin was configured explicitly; no tracked local setting changed.
  Agent requests use a 30-second SDK timeout and no automatic retries. UI locks
  snapshot selection during operations and resets results when scope changes.
- M4: corpus/tasks frozen in `b1fb839` before measurement. Scripted real-DB cases
  take 3/5/6 calls, find every expected source, and have reviewed prewritten answers.
  Qwen key was available: first live cases completed with 6/4/4 tools; all found
  evidence, but strict source/decision grounding failed all three. A general
  prompt constraint trial on identical frozen inputs completed with 6/4/7 tools;
  one answer passed strict source review, two retained unsupported universal/intent
  claims. Preserve both reports and exact-answer/evidence-hashed review verdicts.
  The small non-repeated comparison does not establish accuracy or causal gain.
- Full live suite: 196 passed (includes API + tools → loop → final trace and
  disposable migration replay). Ordinary suite: 180 passed / 16 DB skips.
  Alembic current/check and Ruff passed. V1 vector/hybrid metrics and V2 structural
  expectations reproduced unchanged. V1 CLI lacks --output; corrected the initial
  unsupported invocation by saving its stdout, then both commands succeeded.
- Final documentation/audit remains. No new dependencies or implementation blocker.
  Observed LLM conclusion/grounding failures remain explicit baseline limitations.

### M4 review finding

An escaped-source regression exposed a bounding defect: oversized JSON escaping
could discard an entire read result. Fixed by retaining the largest content prefix
that fits the complete JSON bound; regression now requires nonempty saved source.
All 70 focused V3 tests passed against live PostgreSQL after the fix; Ruff passed.
