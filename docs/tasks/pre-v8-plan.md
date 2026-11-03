# Pre-V8 engineering execution plan

Authorization: [owner goal](../goals/pre-v8-engineering.md), 2026-11-03.
Baseline 40ccf6f, clean codex/v6-evaluation, now codex/pre-v8-engineering.
Read-only fetch: origin/main 5316cf8 (V6 merge), tracked V6 branch 5dac7e9.
Preserve local JSX fix. No remote writes, public deployment or V8 authorized.

| Milestone | State | Acceptance |
| --- | --- | --- |
| M0 Preflight | Complete | Existing V4/V5/V6 boundaries, baseline DB/Docker/tests, history |
| A1 Packaging/config | Implemented/validated locally | Locked API/Web images, loopback Compose, migration gate, explicit deployment settings, no daemon socket |
| A2 Diagnostics/reliability | Implemented/validated locally | Correlation-safe JSON logs, measured operations, bounded failures, cleanup/restart |
| A3 CI/deployment | Local validation; hosted CI unexecuted | Minimal-permission workflow, real local equivalent checks, smoke/restart/backup/restore |
| B1 Trusted profiles | Implemented; regression passed | Commit-pinned approved Python source/test configurations, reuse workspace/sandbox, fail closed |
| B2 Real repositories | Deterministic Docker passed; live trial running | Two independent real Python repositories; success/failure/refusal/escape scenarios |
| C Integration | Pending | Existing binding/repair/verification/proposal pipeline, exact approval and fake remote recovery |
| D Acceptance | Pending | Full regression, frozen/live evaluation, security review, accurate final evidence |

Inspection: existing profiles require exact frozen sources and issue; publication
Git tree calculation supports flat files only. Generalization must extend these,
not create parallel approval/execution systems. Sandbox already enforces nonroot,
network none, immutable image, caps/memory/pids/time limits and exact revisions.
API container must never mount Docker socket; sandbox capability remains explicitly
unavailable there until a separately safe execution arrangement exists. Host-local
workflow stays supported. No new executor service or trust-boundary expansion.

Validation: Docker 29.7.2 available, prepared v4 sandbox image 71aebb88109c;
existing database started without volume deletion. Frontend npm run build passed.
Ordinary backend baseline running. Live GitHub workflow execution unavailable
without remote write authorization; local checks cannot be called GitHub CI PASS.

2026-11-03 M0 baseline complete: ordinary 310 passed /64 opt-in skips;
live DB/Docker 373 passed /1 disabled online MCP skip; Ruff, Alembic
0008 current/check and npm build passed. Fetch confirms main only adds V6 merge.

A1 implemented and actually started: immutable API/Web base images, locked
installs, nonroot/read-only containers, isolated app override Compose, migration
completion gate, loopback proxy, no Docker CLI/socket/credentials in API image.
Database/API/Web healthy. HTTP ingest -> 19 chunks -> deterministic RAG with one
citation passed and survived API/Web stop/start (repo 1187 / snapshot 1383).
Runtime inspect confirms API no published port, read-only /repositories only;
image scan found no .env/Git/node_modules. Source contexts reduced to ~623KB API
and ~62KB changed Web input. Initial malformed tmpfs YAML was rejected by Docker,
quoted list entries corrected before successful startup. No isolation relaxation.
Backup restored into NEW pre_v8_restore_20261103 DB: Alembic 0008 and 17 snapshots
read back. Original volume untouched. Repeat final quiescent acceptance pending.

A2 initial regression after metadata diagnostics/config changes: 376 passed /
1 disabled live MCP skip, 160.17s. Focused config/logging/provider tests 28 passed.
Further bounded SDK defaults/investigation log changes need final regression.
No package/schema additions. npm audit found two existing high dependencies;
compatible lock-only patches Vite 7.3.7 and source-map-js 1.2.2 yield zero findings.

A3 CI defined with exact verified action SHAs, locked tooling, DB/Sandbox tests,
image builds and isolated Compose smoke. NOT run on GitHub (no remote writes).
Local deployment operations/backup guidance exists; browser UI check pending.
Phase B repository identities requested asynchronously under explicit trust rule;
configuration/guard implementation can proceed without executing external code.

B1/B2 progress: owner explicitly approved autonomous selection/review of two small
public pure-Python repositories (no further selection approval needed). Selected
pallets/itsdangerous 1a9b8d1f9968eb248bda69f39d373a6330b692ba Issue #126,
and more-itertools/more-itertools 64be96ceb2a6e836f76f069f4a96d2394d59fd0c
Issue #1336. Python package-source projections exported with licenses, source
hashes and read-only Git provenance; no source import/install on host. Reviewed
stdlib/optional imports, packaging metadata and protected independent tests.
New pre-v8 sandbox immutable image 8aa71903f763491db90e2fa2ec4f60944b57aef16dd874aaf8817d43e880d958;
original v4 image/tag preserved. Root/src layouts only, no installer/shell options.
Policy file is operator-owned and SHA256-approved; changed source/image/validation
fails closed. Patch source evidence limit may be explicitly configured up to 1MB,
keeping frozen 40KB defaults and 40KB diff bound. This follows observed rejection
of a real 170350-byte module; no filesystem/execution isolation relaxation.

Actual direct Docker probe: ItsDangerous 3 failing/5 passing -> 8 passing;
more-itertools 6 failing/3 passing -> 9 passing. Initial report preserves malformed
new predicate test and evidence-budget refusal; fixed test and controlled budget
then reran. Actual full tool-loop tests plus refusal/stale-revision/escape guards:
15 passed with RUN_TRUSTED_PYTHON_TESTS=1. Earlier full DB/Docker suite 389 passed/
1 disabled MCP skip before the last two live tests were collected; final D will
rerun with all opt-ins and current code. Frontend build passed after type updates.
Current full tool-loop/registry/patch/API focus 35 passed. No new dependencies/schema.
Configured dated Qwen key is available; bounded two-case live trial started once,
separate from deterministic patch evidence. C integration and D still outstanding.

Local milestone commits: e864545 authorization/plan, aeb0e69 security lock fixes,
bcd7b03 packaging/config/CI, 544f741 correlated diagnostics/provider deadlines.
Browser local-stack Q&A/citation flow confirmed; screenshot stored under evaluation.

Live Qwen trial completed (no scripted fallback or retry): ItsDangerous stopped
provider_failure at revision 0 after 16 tool steps, independent 5/8 passed;
more-itertools exhausted max_steps at revision 1 after 18 tool steps, independent
9/9 passed but incomplete_repair. Both workspaces cleaned. Evidence
pre-v8-python-live.json retains full traces; no general success claim. The trial
used approved task descriptions, not subsequently retrieved original Issue bodies.
C will bind original Issue data separately; do not mix identities in evaluation.
Quiescent database restore to NEW pre_v8_restore_verified_20261103 succeeded:
17 snapshots, row JSON aggregate MD5 387b77cc39bee8ca0267329d514eec1d matches
original and restored DB. Original volume untouched; API/Web restarted afterward.
Nested Git tree provenance tests 8 passed, not yet wired to publication.

C1 integration now implemented in the existing modules: optional operator profiles
in persist_binding, original Issue body provenance, bound commit validation,
resolve_bound_issue -> actual index/Agent/workspace/Docker -> persisted run,
prepare_proposal -> precise hash/approval and disabled remote-write gate. Git
nested trees preserve baseline blobs/modes (including untouched files outside the
executable projection); new plans carry full baseline metadata. Legacy plan JSON
omits new empty fields so historical exact approval hashes remain unchanged.
Actual read-only official MCP imports succeeded for BOTH public repositories:
bindings 2138/2140 and snapshots 1566/1568. Evidence pre-v8-trusted-import.json.
No remote writes. Original issue bodies differ from earlier reviewed task summaries;
new policy SHA256 fa66ccada24d38ada2d50d2a1164e77b1812a64db8ba98ff04236e37296e5555.
Earlier model/probe reports retain old policy hashes and are historical trials.
Focused C regression 47 passed, real DB/Docker exact proposal path included;
further nested fake-remote recovery/UI/full regression still pending.
Current publication guard still requires private repository/owner identity/main
baseline. Public historical upstreams are read/repair/proposal inputs only; no
extension of write permissions or public-target publication is authorized.

C1 actual bound deterministic repairs/proposals completed for both real imported
Issues, using original Issue bodies and exact approved source/profile identity.
Run/plan evidence: pre-v8-bound-proposals.json. Proposals fc73598c6f744186b2d7af63f802486c
and f09d2f51abce4e078f3bc86e86903296 remain awaiting_approval. No approval or remote
mutation performed. Public historical targets are explicitly not publishable under
the unchanged private-owner/main guard; limitations are attached to each proposal.
Configured-secret scan across all pre-v8 evidence found zero matches.
Current focused MCP/profile/binding/proposal/publication regression: 85 passed /
1 check without RUN_SANDBOX_TESTS skipped, 49.13s. Follow-up narrower suite 36 passed.
Frontend build passed after optional baseline tree metadata type/guard updates.
Remaining: nested fake-remote publication/recovery tests, UI trusted profile selection,
V6 real-repository harness integration, current full regression and security audit,
controlled deployment limitations/CI execution status, final accurate report. Do not
mark Phase C/D or the complete goal achieved yet.

C2/C3 progress: five nested fake-remote publication/reconciliation cases passed
(real saved Docker evidence, simulated remote only). Tree/commit/branch/PR ambiguous
outcomes reconcile without duplicated effects; partial patches preserve all
unchanged baseline blobs and file modes. Public targets remain rejected. Current
UI now lists approved/allowlisted Python Issue identities, imports through the
existing binding path, and presents persisted repair/proposal/limitations. Browser
inspection at 127.0.0.1:5174 with host API 8001 confirmed both choices, a saved
ItsDangerous repair, complete diff, awaiting_approval, and disabled approval/publish
before human confirmation. No approval checkbox or publish action was used.
Evidence screenshot: pre-v8-trusted-review-browser.png. Temporary API PID 29528 /
exec session 44676, Vite session 43209 are task-owned loopback-only test services.
Registry catalog test confirms unapproved/denied profiles are hidden, no test code
or image metadata leaks, and changed policy bytes fail closed (14 passed /2 real
Docker skips without opt-in). Frontend TypeScript/production build passed.
Full DB/Docker/trusted suite on 8b97521: 400 passed /1 disabled online MCP skip,
154.71s; this predates the six new catalog/fake-publication tests. Final D rerun
must use the current committed code and all applicable opt-ins.
