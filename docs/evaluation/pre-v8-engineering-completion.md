# Pre-V8 engineering acceptance report — 2026-11-03

**Status: incomplete; approved Broker implemented, final container workflow/regression pending.**
Do not mark the full Goal or V8 readiness achieved. Local engineering, real corpus
repair/review integration and evaluation are implemented and verified as below.
No new remote write or public deployment was authorized or executed.

## Requirement audit

| Goal item | Current evidence | Acceptance |
| --- | --- | --- |
| Preflight | clean 40ccf6f baseline, read-only fetch (origin/main 5316cf8), dedicated codex/pre-v8-engineering, saved owner Goal and execution plan | verified |
| A1 packaging | locked API/Web Docker builds, pinned base images, nonroot/readonly roots, loopback Compose, migration completion gate, persistent DB volume, original host development retained | verified packaging; container repair unavailable |
| A2 configuration | typed development/test/deployment Settings, explicit deployment core/provider/model settings, safe errors, .env.example, approved policy path plus exact SHA256 | verified |
| A3 CI | pinned action SHAs, contents-read permission, locked tools, DB/pgvector/migrations/Ruff/tests/build/images/Compose smoke; isolated runtime policy on rebuilt image verified locally | defined and locally validated; NOT executed on GitHub |
| A4 diagnostics | correlated JSON request route/status/duration; retrieval/LLM/tool/Sandbox timing and safe outcomes; existing traces/reports retained | verified metadata behavior; no raw request/source/exception logging |
| A5 reliability | fixed provider deadlines/no blind retries; bounded Agent/Sandbox resources; force cleanup on timeout/cancellation; precise publication reconciliation/locking; safe unavailable-service behavior; persisted state survives restart | verified tested paths; abrupt-host-death recovery remains operator controlled |
| A6 deployment | new isolated Compose project/volume, clean migrations, healthy DB/API/Web, ingestion/index/RAG smoke and restart preservation; separate backup/restore checks | read workflows verified; complete container repair not achieved |
| B1/B2 real Python support | two original immutable public commits, reviewed package-source projections, exact source/test/image policy, root/src layouts, no installers/shells | verified limited supported layouts; not all Python repositories |
| B3 repair workflow | current reads/plan/baseline failure/atomic patch/current-revision tests/actual diff; stale evidence and path escape denial | verified deterministic and actual Qwen trials |
| B4 isolation | real nonroot/network-none/readonly/caps/seccomp/resources/no socket/no secrets checks and forced cleanup; original V4 regressions retained | verified within trusted Docker host boundary |
| C1 integration | actual official MCP reads -> Issue/commit/Snapshot binding -> existing V4/index/loop/Sandbox -> durable result -> existing exact proposal | verified two actual bound inputs with deterministic Agent execution |
| C2 approval | complete diff, plans, baseline/revision/tests/commit/branch/PR metadata, exact digest and limitations; precise tamper/origin/policy tests; browser verification | verified local review/approval mechanisms; actual new proposals remain awaiting approval |
| C3 publication | same V5 pipeline with nested Git blobs/modes; precise parent/tree/ref/PR checks; five nested ambiguity/retry fake-remote cases | fake contracts verified; new actual remote writes NOT executed |
| D1 regression | final 414 passed /1 disabled online MCP skip; Ruff, build, Alembic head/check/replay, current images/fresh Compose/smoke; frozen V6 CLI | verified listed scopes; skip is not PASS |
| D2 security | dedicated evidence/risk review, credential scan zero matches, no public services or daemon in app container | reviewed; see remaining boundary below |
| D3 evaluation | existing V6 CaseResult/graders/aggregate/report/compare reused by trusted-python command, independent final tests and owned source/Snapshot/DB cleanup | verified; previous failures and unsupported claims retained |
| D4 docs/scope | README/AGENTS/PROJECT, deployment/trusted Python guides, actual reports, security review, plan and this audit | updated; full acceptance still incomplete |

## Architecture and implemented behavior

React -> explicit HTTP API -> FastAPI -> SQLAlchemy/PostgreSQL/pgvector. Approved
operator policy binds repository/commit, original Issue identity/body, source hashes,
edit permissions, independent tests, image, layout and bounded evidence size.
Actual GitHub MCP read adapters validate the allowed repository and immutable bytes,
then reuse persisted Issue/Snapshot binding. Existing V1/V2 indexes and V4 bounded
read/plan/patch/test loop operate only in a private copied workspace. Tests bind
workspace/revision/policy/image and actual code bytes. V5 persists results and
rebuilds exact proposals before approval/publication. Nested Git trees retain all
unchanged baseline files/modes outside the executable projection. No second Agent,
approval store, publication system, scheduler, cache or queue was introduced.

Application containers and code-test containers are separate. Application containers
do not receive Docker CLI/socket or host credentials. That safe boundary currently
means repair is supported by the host-local API, not by the container API. The new
local Broker in [approved decision](../tasks/pre-v8-executor-decision.md) is now
implemented. Actual authenticated container API probes repair both projects,
independently pass 8/8 and 9/9 tests, reject unauthorized/profile/path/command/
oversized/concurrent requests, and enforce timeout/cleanup. Crash/restart tests
verify exclusive process locking, owned orphan cleanup and persistent ambiguous
request denial. The separate private Web/API Unix transport and complete HTTP
workflow still require final validation; older acceptance rows below remain
historical evidence until the final audit is updated.

## Real-world evaluation and failures

| Input | Immutable baseline | Actual measurements |
| --- | --- | --- |
| pallets/itsdangerous Issue 126 | 1a9b8d1f9968eb248bda69f39d373a6330b692ba | baseline 3 failed/5 passed; final independent 8 passed |
| more-itertools/more-itertools Issue 1336 | 64be96ceb2a6e836f76f069f4a96d2394d59fd0c | baseline 6 failed/3 passed; final independent 9 passed |
| Separate clock-drift ambiguity | same approved ItsDangerous source | revision zero, no patch/tests, needs_owner_decision |

Sources are all package Python modules at these commits (9 and 3 files), not whole
working repositories or upstream full test suites. Original licenses and Git
blob/tree provenance are retained. Third-party code was never installed/imported/
executed on the host; only reviewed Docker tests execute it. Simplejson is not
installed; ItsDangerous uses its stdlib fallback. No other runtime dependencies
or external services were installed for these packages.

On committed code 5963068, the scripted harness measured 3/3 task execution,
2/2 repairs and 1/1 safe decisions with real Docker. The original-Issue actual
`qwen3.7-flash-2026-07-15` run also measured these outcomes. Tool calls were 17/10/1,
model turns 18/11/2, per-case elapsed time 85963.955/63756.712/12864.342 ms including
adapter overhead. Tokens/cost are unavailable, not zero. Independent tests run again
after the model stops. Exact report/config/code/policy fingerprints are saved.

The timestamp repair passed tests but its final prose stated a reversed valid
timestamp interval. Exact-evidence Codex review marks that explanation unsupported;
the other two explanations were supported by source/trace. This is Codex review,
not independent human judgment. Task execution and explanation quality are separate
metrics. Raw and reviewed results: [live](pre-v8-harness-python-live.json),
[reviewed](pre-v8-harness-python-live-reviewed.json),
[scripted](pre-v8-harness-python-scripted.json).

Earlier reviewed-task-summary Qwen attempts remain separate: ItsDangerous had a
provider failure at revision zero (5/8 tests passed); more-itertools exhausted model
turns despite a 9/9 passing patch and remained incomplete_repair. Those inputs and
policy identities differ from the later original-Issue corpus. They were not
pooled, deleted or relabeled successful. Initial probe's malformed new test and
40KB evidence-budget refusal are also preserved. The real 170350-byte module
justified an explicit 500KB profile budget, with a 1MB server ceiling; old 40KB
defaults and the 40KB diff cap remain. These tiny cases prove no general success
rate or measured product improvement.

## Actual validation

From apps/api unless noted. Full opt-in suite sets RUN_DATABASE_TESTS=1,
RUN_SANDBOX_TESTS=1 and RUN_TRUSTED_PYTHON_TESTS=1. Shell outputs are retained in
the chat; executable evidence is in tests and linked JSON reports.

| Command/check actually run | Result |
| --- | --- |
| Initial uv run pytest -q | 310 passed /64 opt-in skips |
| Initial full DB/Docker suite | 373 passed /1 online MCP skip |
| Intermediate full suites | 376, 389, 400, 406 passed respectively; each had 1 disabled online MCP skip; code versions differ |
| Final uv run pytest -q on 9a9286b | **414 passed /1 skipped**, 171.18s; existing Starlette/AnyIO deprecation warning |
| New grader/owned adapter + V6 focused suite | 39 passed with live DB/Docker |
| Rebuilt-image CI runtime policy fixture simulation | 30 passed with real DB/Docker; immutable historical fixtures unchanged |
| uv run ruff check src tests migrations | passed |
| uv run alembic current / check | 0008_github_publications head; no upgrade operations |
| Disposable clean migration replay in full suite | all migrations to head, sentinel preservation, pgvector, downgrade/upgrade replay and no drift verified; only uniquely owned test DB removed |
| npm run build | TypeScript and production Vite build passed; no separate frontend lint/test scripts configured |
| npm audit / lock security fix | zero findings after compatible Vite 7.3.7/source-map-js 1.2.2 updates; initial two high findings retained in plan |
| Docker builds + new repopilot-pre-v8-acceptance Compose project | API/Web build passed; brand-new DB volume, clean migrations, all services healthy |
| python scripts/compose_smoke.py --base-url http://127.0.0.1:8081 | repo/snapshot 1, 19 chunks, one deterministic answer citation; same IDs after restart |
| Backup/restore to newly created verification DB | 17 snapshot rows; original/restored row aggregate MD5 both 387b77cc39bee8ca0267329d514eec1d; original volume untouched |
| Official GitHub MCP trusted imports | both repositories bound at exact commits; [actual read evidence](pre-v8-trusted-import.json), zero remote writes |
| Bound repair -> proposal | two deterministic real DB/Docker repairs and awaiting-approval plans; [evidence](pre-v8-bound-proposals.json) |
| Existing frozen V6 CLI | original 17 tasks: retrieval/structure/resolution pass, five generated semantic outputs explicitly unverified; [report](pre-v8-v6-frozen-regression.json) |
| trusted-python --mode scripted / live | separate actual three-task runs, raw and exact-output reviewed evidence above |
| Browser on current local host API/Web | approved choices, saved result, full diff/target/revision/commit/PR/limitation text, awaiting approval; approval/publish controls disabled before confirmation; no approval/publication action used |
| Git diff checks / configured-secret scans | clean diffs; zero actual configured token/key matches in generated evidence |
| GitHub-hosted workflow | **NOT EXECUTED**; local results must not be called hosted CI PASS |

## Changed files, dependencies and Git

Main changes: API/Web Dockerfiles, .dockerignore, compose.app.yaml, nginx.conf,
.github/workflows/ci.yml, Settings, diagnostics, bounded provider defaults,
resolution profiles/models/service/patch/tools/Sandbox runner, trusted policy loader,
GitHub binding/resolution/proposals/tree verification/Git API, profile catalog/import
API, React GitHub/review types and UI, evaluation trusted adapter/CLI/grader, tests,
licensed reviewed corpus, deployment/trusted Python guides and actual evidence.
No Python package, frontend package family, migration or schema added. Existing
npm lock entries were patched for published advisories. uv is pinned as build
tooling; Nginx is the static/proxy runtime and Node the frontend build stage.

Local commits: e864545 authorization, aeb0e69 security lock fixes, bcd7b03 packaging/
CI/config, 544f741 metadata diagnostics/provider limits, b7d5f82 trusted profiles,
8b97521 binding/repair/proposals, 29fd645 UI/recovery, 270e8d7 frozen evaluation,
5963068 real Python harness, 9a9286b live evidence/CI runtime policy isolation.
No push, PR, merge, destructive history rewrite or unapproved data deletion.

## Remaining work, risk and V8 readiness

The full Goal is **not complete**. Complete repair from the container API is not
available. A broker would create a new service holding Docker authority and must
be approved under the Goal's mandatory security escalation rule; the alternative
is an explicit owner acceptance of host-local execution as the deployment boundary.
See the concrete [decision proposal](../tasks/pre-v8-executor-decision.md).

Hosted CI remains unexecuted; no claim of GitHub CI success is made. Public upstream
historical plans cannot publish through the unchanged private-owner/current-main
guard. New actual remote publication is unapproved and intentionally not performed.
Sandbox/Python tests are not adversarial attestation. Host crashes can leave
in-flight state requiring operator review; automatic replay of writes is forbidden.
See [security review](pre-v8-security-review.md) for tested guarantees and risks.

No V8 packaging, public demo, public hosting, new Agent framework, multi-agent
system, Redis, queue, Kubernetes or unrelated feature was introduced. **Stop before
V8. V8 readiness is not yet proven while the deployment acceptance decision remains.**
