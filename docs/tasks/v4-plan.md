# RepoPilot V4 Execution Plan

## Active goal and current state

Implement the [authorized V4 goal](../goals/v4-issue-resolution-agent.md).
**M1-M5 complete; M6 incomplete, waiting for Qwen quota restoration.**
Do not declare V4 complete or enter V5. Authorization persists for V4 resumption.
Full evidence, failures, risks and acceptance mapping:
[implementation/acceptance status](../evaluation/v4-issue-resolution-status.md).

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| M0 | Verify V3 baseline, environment, goal and plan | Complete |
| M1 | Owned saved-source workspaces and frozen fixtures | Complete |
| M2 | Atomic bounded patch, current reads, actual diff | Complete |
| M3 | Restricted Docker/pytest, real isolation checks | Complete |
| M4 | Public plan and bounded repair/retest loop | Complete |
| M5 | Separate typed resolve API and existing React workflow | Complete |
| M6 | Frozen model evaluation, regressions, final acceptance | Incomplete: real-model negative revalidation blocked |

## Decisions and scope

- Preserve V1/V2 indexes and V3 investigation; use existing provider/protocol helpers.
- Only backend-approved frozen Python profiles execute. A saved Snapshot alone
  is not an arbitrary executable repository. Verify saved bytes and Snapshot hash.
- Temporary workspace is private, separately owned and outside RepoPilot. Original
  source/Snapshot stay unchanged. Complete revisions make failed patches atomic.
- One exact-context apply_patch interface. Tests/config/secrets remain denied.
- Public plan + actual failing baseline required before writes; reads see current
  revision; indexed evidence is labeled baseline-only after modifications.
- No host fallback. Immutable trusted image, read-only mounts, no network/secrets,
  unprivileged/capability/seccomp/resource restrictions, bounded streams/cleanup.
- Server derives status from exact-revision independent tests and expected counts;
  completed execution/final prose alone never proves repair correctness.
- No GitHub/MCP, arbitrary shell/repository/dependencies, production architecture,
  queues/workers/global state/UI frameworks, or multi-agent implementation.

## Verified progress

- M0 (2026-10-21): exact baseline d1ca767 on clean main. Ordinary tests 180 passed/
  16 skips; full live 196 passed, Ruff/build/Alembic and V1-V3 baselines passed.
  Docker initially crashed, then recovered externally; Linux isolation probe passed.
- M1-M3: 21, 31 and combined 39 focused checks passed. Actual Golden baselines
  fail (fees 4/8, dispatch 2/11) and reference patches pass (8/11 tests respectively).
  Source/tests/issue intent were frozen before model evaluation.
- M4 full live suite: 245 passed. Fixed DB-collation versus V1 Python sort ordering
  in V4 Snapshot verification; V1 identity format unchanged.
- M5 API/V3 API checks: 22 passed; web build passed. Initial real Qwen browser run
  failed nested patch schemas (18 turns, zero edits). Inlined fields, precise safe
  errors and invalid-attempt accounting fixed that interface. Regression 51 passed.
  Real browser rerun: one Qwen patch, 8 passing tests at revision 1, cleanup and
  original/modified source verified; screenshot retained. Prose had a cent/unit error.
- M6 scripted evaluation: all three cases meet conditions, including deliberate
  failed patch/repair. Full Qwen: both positive repairs verified; negative safely
  stopped on unavailable test tool instead of deciding intent. Preserve all reports.
- Profile definitions/dispatch now omit unavailable write/test tools. Regression
  covers the exact failure; source/test ground truth unchanged. Targeted real Qwen
  trial and independent retry failed at provider request 1. Safe diagnostic confirms
  HTTP 403 PERMISSION_DENIED: free quota exhausted. Do not switch models or alter
  the frozen negative criterion to claim completion.
- Final self-review isolates disposable DB integration source and exact owned
  cleanup assertions. Actual private workspace ACL admits SYSTEM/Admin/OWNER only.

## Latest actual validation (2026-10-22)

| Check | Result |
| --- | --- |
| Ordinary uv run pytest -q | 238 passed / 24 opt-in skips |
| RUN_DATABASE_TESTS=1 RUN_SANDBOX_TESTS=1 uv run pytest -q | 262 passed |
| Ruff src/tests/migrations | Passed |
| Alembic current/check and disposable replay | Head 0005; no pending changes; replay passed |
| npm run build | Passed |
| Frozen V1 vector/hybrid, V2 structure, V3 scripted CLIs | Baseline results preserved, reports saved |
| Actual positive Qwen repairs and browser workflow | Verified |
| Corrected negative real Qwen criterion | NOT PASSED: quota exhausted |

Final live integration strengthening also exercised the actual resolve HTTP route
against PostgreSQL (scripted owner decision, no service mocking); two focused
DB/Docker/HTTP checks passed. This is not a substitute for the blocked Qwen trial.

Existing AnyIO warning remains. Initial missing PYTHONPATH, unexpanded PowerShell
pytest glob and failed live runs were corrected or explicitly retained as failures;
they are not reported as passing. No app dependency/migration/lockfile added.

## Remaining work and resume

1. Owner restores Qwen capacity; billing/account changes are outside this goal.
2. Re-run frozen ambiguous-cap with existing Qwen and immutable sandbox image:
   PYTHONPATH=src uv run python -m repopilot.evaluation.resolution --mode qwen
   --case ambiguous-cap --output ../../docs/evaluation/v4-resolution-qwen-ambiguity-resumed.json
   (Use PowerShell environment syntax on Windows.)
3. Review/hash the exact result against needs_owner_decision with zero unsafe
   attempts/changes. Diagnose within existing scope if the criterion still fails.
4. Recheck any changed implementation, finalize acceptance/documentation and
   meaningful commit, then stop at V4/V5. No completion declaration before this.

Milestone commits: 11d38c9, 7dc47e7, 8f933cf, 77f6a2c, 69a9acc,
46a261e, dec07c1, 717ede1, 5a3c585. Full details are in the linked status report.
