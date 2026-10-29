# V6 execution plan

Authorized scope: [goal](../goals/v6-evaluation.md). Baseline: dd1cfb5,
verified origin/main after read-only fetch and clean fast-forward. Branch:
`codex/v6-evaluation`. No remote writes authorized. Stop before V7.

| Milestone | State | Work |
| --- | --- | --- |
| M0 | In progress | Inventory V1 retrieval, V2 structure, V3 investigation, V4 repair; baseline checks |
| M1 | Pending | Typed versioned manifest linking unchanged frozen datasets; small RAG checks |
| M2 | Pending | Independent grading, applicability/denominators, missing measurements |
| M3 | Pending | CLI adapters, actual pipelines, per-case errors and owned cleanup |
| M4 | Pending | Scripted DB/Docker and bounded live Qwen pass; failure evidence |
| M5 | Pending | JSON/Markdown and guarded comparison |
| M6 | Pending | Full regressions, security review, completion evidence |

Inventory: evaluation/{runner,structural,agent,resolution}.py already implement
actual pipelines. V1 metrics must be reused. V2/V3 frozen manifests already verify
normalized content; V4 pins its manifest and protected tests. V3 grounding reviews
are exact-answer hashes. Existing providers do not expose usage consistently:
V6 will mark tokens/cost unavailable. Historical failures remain evidence.
Old V1–V3 entry points persist fixture snapshots; the unified harness will give
these adapters fresh evaluation-owned source paths and delete only those rows.
No new service, API, schema, dependency, judge model or product-agent capability.

Preflight actually executed: uv run pytest -q: 267 passed/63 opt-in skips;
npm run build: pass. Docker Linux and healthy Compose DB, immutable prepared image
71aebb88109cbb7c2eb535ef4321a4b9d23b886c0c14625bafaeb9e78b5fea5f available.
Database/sandbox full suite, Ruff and migrations running. Read goal/plan/report
for V4/V5 and inspected provider, evaluation, source, test and Git contracts.

M0 completed: database/sandbox suite 329 passed / 1 explicitly disabled live MCP
skip; Ruff passed; Alembic 0008 head/check no drift, disposable migration replay
covered by tests. No live MCP enabled for V6. Initial RAG harness smoke exposed a
scripted citation header parser mismatch (E999 rejected); fixed the adapter to
parse the actual context format. This was evaluator wiring, not model evidence.
M1/M2 implemented: 17 pinned tasks (8 retrieval, 1 structural suite, 3 investigation,
2 RAG source checks, 3 issues); historical fixtures/hashes unchanged. M3/M5 initial
runner and reporting implemented, pending regression/self-review before commit.

M1–M3/M5 engineering review: typed 17-task manifest; pinned normalized input bytes,
source file-set checks, legacy entry-point selection without ground-truth changes,
actual RAG pipeline adapter, independent exact-revision/count/isolation test grader,
separate safe-decision score, nullable usage/cost, JSON/Markdown and strict compatible
run comparison. Exact-evidence review import records provenance. Nine historical
V3/V4 reviews verified against saved output hashes, including two unsupported V3
claims; history stays separate from current metrics. Initial full scripted run:
8 retrieval and structural suite passed, 5 generated answers remain unreviewed,
2 actual Docker repairs and 1 safe decision passed. Final scoring aggregation and
additional review tests were added afterward; final runs will pin committed code.

M4 live pass completed once on qwen3.7-flash-2026-07-15: fee-days verified (8 tests),
dispatch-preconditions exhausted max_steps/incomplete repair, ambiguous-cap correct
zero-change owner decision. Five investigation/RAG outputs initially unreviewed;
all five discovered evidence and valid source-identical citations. This negative
repair result is preserved, not rerun to obtain success. No provider failure.

Self-review found the NEW RAG fee annotation mistakenly described the V4 daily
formula, while V1 frozen invoices.py uses weekly 1% capped at 10%. Corrected only
new V6 annotation, incremented dataset version to 2 and changed canonical hash;
original V1–V4 fixtures and hashes untouched. Version-1 script/live reports remain
historical measured trials and cannot compare to final version 2. Final script and
two bounded RAG live calls will validate the corrected version; no Issue retries.
Added per-attempt patch-application denominator alongside task-level applicability.
Initial focused test run had a GBK decoding failure in a test reading Unicode JSON;
explicit UTF-8 fixed it; rerun 45 passed and Ruff passed. Fix is a separate commit.

Self-review correction: live dispatch independently passed 11/11 at revision 1,
but exhausted 18 model turns and retained incomplete_repair. Preserve that bounded
Task failure while reporting independent-test success; removed the erroneous
independent_test_failure classification for this exact situation. New regression
covers it. Claim-support quality is null when no concrete review exists; coverage
and reviewed denominator are explicit. Review imports fingerprint grader code.
Focused current suite: 31 passed with real owned-DB cleanup; Ruff passed.
First full V6 DB/Docker suite: 358 passed / 1 disabled online MCP skip before the
last two regression tests; final rerun follows the scoring corrections.
