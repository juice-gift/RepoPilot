# V6 Evaluation System completion — 2026-10-29

Engineering implementation complete; evaluation validated. M0–M6 complete.
The live quality failures below are measured limitations, not hidden acceptance
blockers. No mandatory infrastructure/credential check remains blocked. Stop at
V6/V7. Optional online MCP identity checks were intentionally not enabled.

## Milestones and architecture

M0 verified clean local main, fetched origin read-only, fast-forwarded from 0308e8a
to the merged V5 main dd1cfb5 and created codex/v6-evaluation. Read AGENTS/PROJECT,
V4/V5 goals/plans/completion evidence and inspected source, fixtures/tests/history.
M1 introduced a typed 17-task dataset, frozen source/file-set identities and
explicit expected outcomes. M2 added independent graders and applicability-aware
metrics. M3 connected existing real pipelines through narrow owned-input adapters.
M4 ran scripted and bounded Qwen evaluations. M5 produced JSON/Markdown and guarded
comparison/review commands. M6 completed regression, scope/security review and docs.

Data flow: validated versioned dataset → fresh copied source → existing V1
retrieval / V2 structure / V3 investigation / V1 RAG / V4 resolution + restricted
Docker tests → independent evidence graders → checkpointed per-case JSON and
Markdown → compatible-run comparison or exact-output source review. Evaluation
logic lives in the existing Python evaluation package. Only V1/V3 selection
parameters were added, retaining old defaults and interfaces. Unique temporary
source paths and exact-path DB cleanup preserve existing application snapshots;
V4 retains its existing profile/workspace/container lifecycle.

No service, API, database schema, frontend dashboard, dependency or migration added.
The underlying React/FastAPI/PostgreSQL/pgvector and MCP/GitHub boundaries remain.

## Actual results and limitations

Final dataset: **version 2**, 17 tasks, canonical SHA256
`25d0666fe7666424cb84256408b3ae41da7b99fde22c9f3e838c8be5b1f3cc18`.
Code under final scripted evaluation: **4e9f710**; relevant code/config fingerprints
are in JSON. Dirty flag truthfully includes in-progress documentation/evidence.

| Measurement | Actual result | Evidence |
| --- | --- | --- |
| Final scripted suite | 12 passed, 5 unverified semantic outputs; 17 tasks | [JSON](v6-scripted.json), [Markdown](v6-scripted.md) |
| V1 vector, 8 frozen queries | Hit@1/3/5 .75/.875/1; MRR@5 .8375 | [report](v6-vector.json) |
| V1 retained hybrid, 8 queries | Hit/Recall/MRR@1/3/5 all 1 | final scripted report |
| V2 structural suite | definitions 16/16; imports 5/5; resolved targets 8/8; occurrences/status 21/21 | structure/frozen case in scripted JSON |
| V3 scripted | 3/3 required evidence and citation identity checks; semantic claims unreviewed | scripted JSON |
| V4 scripted with real Docker | verified repair 2/2; independent final tests 2/2 (8/11 tests); safe decision 1/1; task success 3/3; patch applications 3/3 attempts | scripted JSON |
| Bounded actual Qwen, 8 tasks on dataset v1 | task success 2/3; completed verified repair 1/2; independent tests 2/2; safe decision 1/1; patch application 2/2 attempts | [raw live run](v6-live-qwen-v1.json), [offline diagnosis](v6-live-qwen-v1-diagnosis.json) |
| Actual live investigation/RAG source review on v1 | evidence/citation validity/identity 5/5; supported claims 3/5 reviewed, 2 unsupported; Issue prose remains unreviewed | [exact-output reviews](v6-live-qwen-v1-diagnosis-reviews.json) |
| Two actual RAG calls on corrected v2 | evidence/citations 2/2; Codex source review 2/2 supported, not independent human judgment | [raw](v6-live-rag.json), [reviewed](v6-live-rag-reviewed.json) |
| Two compatible hybrid retrieval repetitions | no case regressions; all query metrics remain 1 | [comparison](v6-compatible-comparison.json) |

All live calls used the configured `qwen3.7-flash-2026-07-15`. No model switch,
scripted fallback or Issue retry. The v1 full live pass measured 177719.651 ms
including adapter overhead; measured tool calls 53 across 6 applicable agent cases,
model calls 53 across 8 generation/agent cases. V2 RAG follow-up measured 10182.48 ms,
two model calls. Tokens/cost remain **null**, not zero. This is not a general repair
accuracy claim, external embedding benchmark or measured product improvement.

Concrete bad cases:

- `permanent-versus-transient`: valid real citations but the final answer says
  permanent jobs reject regardless of attempt, contradicting the negative-attempt
  exception and omitting token preconditions. Failure: unsupported final claims.
- `documentation-policy-mismatch`: correctly finds 60 versus 300, then invents
  design intent and says documentation must change. Source cannot determine owner
  intent. Failure: unsupported final claims. No code modification occurred.
- `dispatch-preconditions`: actual revision-1 patch passes **11/11** independent
  tests, but the loop exhausts **18 turns**, leaving `incomplete_repair`. Report
  counts independent-test success but bounded-task/verified-repair failure.
  Failure categories: agent limit exhaustion and incomplete task execution,
  **not** independent test failure. Both raw trace and actual patch are retained.
- Initial scripted RAG smoke used the wrong context-header parser and produced
  rejected E999 citations. Fixed before final runs; [initial failure](v6-rag-smoke.json)
  remains evidence of evaluator wiring failure, not LLM failure.

Dataset v1's NEW RAG fee annotation accidentally described V4 daily fees instead
of V1 weekly 1%/10%-cap source. Corrected only that annotation, incremented V6 dataset
to version 2 and changed its hash. Frozen V1–V4 source/ground truth never changed.
V1 dataset SHA256 was
`8497480d95559a947ed3ae9eb3410a33dea384c0dff026e2abe0a482dac7ddda`;
its exact JSON remains recoverable at 76cf942. V1 runs remain labeled v1 and are
not compared with v2. The Issue questions/profiles/source/tests are unchanged.
Offline diagnosis retains original dataset/commit/runtime and records source-report
hash, grader commit/fingerprints and review provenance; it is not another model run.
Reproduction script: [v6-diagnose.py](../tasks/v6-diagnose.py).

Nine historical V3/V4 reviews are independently rebound to original output hashes
and included as separate provenance; the two earlier unsupported V3 conclusions
and V4 quota failures remain visible and never enter current-run numerators.
Source reviews here are **Codex review, not independent human review**. Untouched
outputs remain unverified. The three-Issue corpus cannot establish broad reliability.

## Validation actually executed

Commands below use PowerShell, run from apps/api except frontend/git commands.
For DB/Docker validation:
`$env:RUN_DATABASE_TESTS='1'; $env:RUN_SANDBOX_TESTS='1'`.
For CLI calls: `$env:PYTHONPATH='src'` and
`$env:RESOLUTION_SANDBOX_IMAGE='sha256:71aebb88109cbb7c2eb535ef4321a4b9d23b886c0c14625bafaeb9e78b5fea5f'`.

| Command | Observed result |
| --- | --- |
| Initial `uv run pytest -q` | 267 passed / 63 opt-in skips |
| Initial DB/Docker `uv run pytest -q` | 329 passed / 1 disabled online MCP skip |
| Final DB/Docker `uv run pytest -q` | **360 passed / 1 skipped**, 123.42 s; includes migration replay, DB/API/sandbox and existing V1–V5 regressions |
| Latest focused `uv run pytest tests/test_v6_evaluation.py -q` with database | **31 passed**; covers owned cleanup, integrity, denominators, safe decisions, real-test evidence requirements, failures/reviews/comparison and no GitHub dependency |
| `uv run ruff check src tests migrations` | passed |
| `uv run alembic current`; `uv run alembic check` | 0008_github_publications head; no upgrade operations; disposable replay also passed in full suite |
| `npm run build` from apps/web | passed TypeScript and Vite; no separate lint/test scripts configured |
| `uv run python -m repopilot.evaluation.harness run --output ../../docs/evaluation/v6-scripted.json` | passed execution; five semantic results explicitly unverified |
| Same `run --category retrieval --strategy vector --output ../../docs/evaluation/v6-vector.json` | passed, eight queries |
| `run --mode live --category investigation --category rag --category resolution --output ../../docs/evaluation/v6-live-qwen.json` | actual full bounded pass; exit 1 for incomplete dispatch; preserved as *-v1.json |
| `run --mode live --category rag --output ../../docs/evaluation/v6-live-rag.json` | two actual calls, unreviewed until exact-output review |
| `run --category retrieval --output ../../docs/evaluation/v6-hybrid-repeat-a.json` and corresponding repeat-b | two separate actual deterministic runs passed |
| `compare ../../docs/evaluation/v6-hybrid-repeat-a.json ../../docs/evaluation/v6-hybrid-repeat-b.json --output ../../docs/evaluation/v6-compatible-comparison.json` | compatible, no case changes |
| `compare ../../docs/evaluation/v6-scripted-v1.json ../../docs/evaluation/v6-scripted.json --output ../../docs/evaluation/v6-invalid-comparison.json` | correctly refused with exit 1: incompatible definitions (dataset also differs); no invalid comparison artifact produced |
| `review ../../docs/evaluation/v6-live-rag.json ../../docs/evaluation/v6-live-rag-reviewed-reviews.json --output ../../docs/evaluation/v6-live-rag-cli-reviewed.json` | successful CLI review/report generation |
| `git diff --check`; frozen/dependency/migration path diff; configured-secret scan of generated V6 reports | passed; only new V6 dataset files under evaluation/, zero configured key/token leaks |
| `docker ps --format '{{.Names}}'` | only repopilot-database-1 remains; no evaluation container leak |

An existing Starlette/AnyIO deprecation warning remains. A test initially decoded
UTF-8 JSON with Windows GBK; explicit UTF-8 fixed it (45 focused regressions then
passed). A temporary reviewer fingerprint edit missed its Path import; Ruff/test
caught it, import fixed, and final full suite passed. Initial shell launch path
mistakes were corrected; none are represented as successful runs. No required
check remains failing. Optional real GitHub/MCP checks were not run; they would
require separately opted-in safe configuration and provide no V6 remote-write authority.

## Files, Git, risks and scope audit

Important source: evaluation/contracts.py, grading.py, adapters.py, harness.py,
reviews.py; modest selection additions in runner.py/agent.py. New data:
evaluation/v6-dataset.json/.sha256. Tests: tests/test_v6_evaluation.py. Docs:
AGENTS/README/PROJECT, goal/plan, usage/scoring definitions, actual JSON/Markdown
runs, exact-output reviews, diagnosis script and this completion report.

Branch: codex/v6-evaluation. Local milestone commits: d95f698 (goal/inventory),
76cf942 (harness), 4b3c2b0 (Unicode regression), 980325f (source-correct annotation
and attempts), 4e9f710 (test success versus loop completion/review coverage).
Evidence and closure are committed separately. No push, remote PR, approval,
publication, merge, destructive history rewrite or remote branch change occurred.
No ignored .env was staged. No V7 infrastructure, framework, unrestricted executor,
new Agent or multi-agent system introduced. No new dependencies or migrations.

Concrete remaining risks: small corpus and deterministic embedding limitations;
source review is not independent human judgment; missing provider usage/cost;
conservative comparisons reject changed critical runtime/prompt fingerprints;
Docker availability is required for real repairs and Docker is not absolute
hostile-code isolation. Bounded model loops and unsupported final claims remain
product limitations. Reports contain controlled frozen source only; run on the
trusted single-owner local environment. No mandatory acceptance blocker remains.

Acceptance criteria 1–12 map to the executable CLI, immutable reused datasets,
separate dimensional/negative grading, real exact-revision Docker evidence,
mode/version/provenance metadata, correct missing/failure states, actual reports,
360-test regression, documentation and local milestone history above. V6 is
complete with measured negative model-quality results. **Stop before V7.**
