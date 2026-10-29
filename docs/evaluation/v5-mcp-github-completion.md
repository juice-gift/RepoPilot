# RepoPilot V5 Completion Report

**Completed: 2026-10-29 (Asia/Shanghai). M0–M6 complete. Stop at V5/V6.**

V5 delivers the actual controlled flow: GitHub Issue → immutable repository/Snapshot
binding → existing V4 repair → independent Docker tests → exact human approval →
dedicated commit/branch → official MCP Draft PR. This completion applies to the
approved frozen fixture repository, not arbitrary repositories or general repair accuracy.

## Actual publication and approval

The owner explicitly approved both exact proposals on 2026-10-28 in this chat.
[Approved scope, digests, branches, complete diffs and metadata](../tasks/v5-publication-approval.md)
remain unchanged. Only `juice-gift/repopilot-v5-sandbox` (repository ID 1436602856)
received repair writes. Each commit independently has the sole parent
`b4279c8b4d862817e6778caa5f87da91d29ed2b7` (main).

| Case | Exact approved commit | Actual PR | Final independent tests |
| --- | --- | --- | --- |
| fee-days / Issue 1 | `1abc169665e9a6b6d6e56a2e096f251eefe46bd2` | [Draft #4](https://github.com/juice-gift/repopilot-v5-sandbox/pull/4) | 8 passed |
| dispatch-preconditions / Issue 2 | `114a173431c0ff68f1368615096c24284a5af25d` | [Draft #5](https://github.com/juice-gift/repopilot-v5-sandbox/pull/5) | 11 passed |

Both PRs were created through real official GitHub MCP tools and independently read
back as open, draft and unmerged. Final audit verifies main, exact parent/tree,
100644 file modes, every remote file byte, proposal metadata and Issue contracts.
The final source was compared with the approved plan, then the same bounded patch
was applied to a private workspace from the original frozen Snapshot and retested
with protected local tests. No arbitrary remote checkout was executed. Issue 3
retains its zero-change owner-decision result; no repair PR was created for it.

Evidence: [final live audit](v5-final-live-audit.json),
[fee-days publication](v5-live-publication-fee-days.json),
[dispatch publication and recovery](v5-live-publication-dispatch-preconditions.json),
[original real Qwen results](v5-bound-qwen-resolution.json).

## Files changed and implementation

- `apps/api/src/repopilot/github/client.py`, `probe.py`, `fixture_audit.py`: explicit
  bounded official MCP discovery, schemas, safe transport, credential mapping and
  controlled repository/Issue/commit/file/PR reads.
- `github/binding.py`, `resolution.py`: canonical repo/Issue/commit/Snapshot binding,
  existing V4 resolution integration and durable complete results/digests.
- `github/proposals.py`: derive exact plan from source, patch-history hashes and
  independent final test revision; compute tree/commit before human approval.
- `github/git_api.py`, `pr_client.py`, `publication.py`, `review.py`: fixed Git
  object/ref supplement, exact official MCP PR arguments, approval gates, publication,
  locking, reconciliation, partial errors and review export.
- `apps/api/src/repopilot/api/routes/github.py`, `main.py`: thin typed local-owner
  workflow routes. `config.py`, `.env.example`: safe configuration and separate
  default-empty write allowlist.
- `apps/api/src/repopilot/db/models.py`, migrations 0006–0008: durable Issue/Snapshot
  bindings, resolution runs and publication proposals/approval/outcome state.
- `apps/web/src/GitHubWorkflow.tsx`, `api/github.ts`, `App.tsx`: saved Issue/results,
  exact diff/tests/commit/PR review, deliberate approval, revoke and publish/reconcile.
- Relevant backend policy/protocol/DB/API/Docker tests; reproducible final read-only
  audit under `docs/tasks/v5-final-readonly-audit.py`; evidence, plan and current-stage docs.

React/FastAPI/PostgreSQL and V1–V4 agent/resolution architecture remain. Routes do
not accept model-selected source, executable profiles, destinations or approval.
Remote text, model prose and MCP annotations never grant permissions. Human
approval binds the full immutable SHA256 plan digest, with a separate repository
write allowlist and local loopback/configured-Origin controls.

The official MCP create_branch/push_files tools lack an expected-parent SHA
parameter. The owner-approved fixed Git Data API supplement creates only exact
immutable trees/commits and a create-only dedicated ref. It exposes no update-ref,
PATCH, force, delete, default-branch mutation or merge. Official MCP handles real
reads and PR creation/verification; REST-only integration is not claimed.

## Failure recovery and fixes

The initial fee-days attempt safely stopped before any branch/PR: GitHub returned
the correct newly created tree SHA, but GET could not yet retrieve that unreferenced
object. The next attempt returned the correct commit SHA but rendered its message
without the terminal LF. Both failed attempts and the response diagnostic are
preserved beside the final publication report. The fix verifies full create
responses before creating the exact ref and mandates reachable GET readback before
PR creation. It accepts only the one terminal-LF display normalization while still
requiring the exact approved object SHA, parent, tree, actor and date.

The false stale classification was corrected locally for this unchanged approved
plan after rechecking main and absent head; original human authorization/digest
remained unchanged. No altered plan or baseline was silently approved.

For Issue 2, a deliberately injected client exception followed a successful **actual**
GitHub create-ref. The saved state became retry_needed; recovery read the existing
exact ref/objects and created the single PR. Git mutations were exactly one tree,
one commit and one ref for that run. This is controlled client fault injection over
real remote effects, not a claimed real network outage. Repeated published requests
returned the same saved outcomes without additional Git requests or duplicate PRs.
Local tests additionally exercise collisions, stale main before/during effects,
concurrency locks, timeouts, redirects, tampering and denied approvals/operations.

## Dependencies

V5 adds official `mcp==2.3.0` (protocol), `httpx2` (bounded official transports) and
`jsonschema` (discovered input validation). No LangChain, agent framework, queue,
frontend UI framework or new M4–M6 dependency. Negotiated protocol: 2026-07-28;
actual server identity and schema hashes are retained in live evidence.

## Validation actually executed

- Final `RUN_DATABASE_TESTS=1 RUN_SANDBOX_TESTS=1 RUN_GITHUB_MCP_TESTS=1 uv run pytest -q`:
  **330 passed, zero skips**, including real DB, Docker, official MCP and reversible
  disposable migration replay. One existing AnyIO deprecation warning remains.
- `uv run ruff check src tests migrations` plus final audit script: passed.
- `uv run alembic current` / `check`: 0008 head, no schema drift.
- `npm run build`: TypeScript/Vite production build passed. No frontend lint/test
  script is configured. Browser smoke previously verified saved real results,
  exact plans and disabled unapproved publication controls.
- V1 vector/hybrid, V2 structure, V3 scripted and V4 scripted/real-Docker CLI
  regressions are recorded in `v5-prepublication-*`; frozen results unchanged.
  Scripted cases are not substituted for real Qwen/MCP/GitHub evidence.
- `PYTHONPATH=src uv run python ../../docs/tasks/v5-final-readonly-audit.py`:
  actual main/Issue/PR/source readback and 8/11 independent Docker tests passed;
  workspaces cleaned. Credentials absent from reviewable files; write allowlist
  empty; frozen source/tests/manifest unchanged from main.

On resumption Docker was stopped and initial DB tests could not connect (not passing
results). A direct Docker launch hit a runtime socket startup error. Launching via
the desktop shell restored the engine and existing database without factory reset,
volume deletion or persistent data changes; all relevant checks were rerun above.
An optional broad formatter check earlier reported pre-existing style differences;
unrelated files were left intact. Required lint passes.

## Acceptance audit

| Criterion | Authoritative evidence | Verdict |
| --- | --- | --- |
| 1 Real official MCP discovery/calls | Live read, PR creation and final PR readback; protocol/schema hashes | Pass |
| 2 Correct repo/Issue/code version | Binding migration/import evidence, numeric repo ID, Snapshot 414, pinned main | Pass |
| 3 Denied unauthorized writes | Exact approval digest + server allowlists/arguments, policy/API/tamper/default-ref tests; final empty write allowlist | Pass |
| 4 Complete controlled repair-to-PR | Real Qwen results, independent tests, explicit owner approval, actual Draft PRs 4/5 | Pass |
| 5 Approved tested patch/base matches remote | Exact approved commit SHA, sole parent/tree/modes, all MCP-read bytes, final Docker retests | Pass |
| 6 V1–V4/safety preserved | Full regression, frozen CLI reports, unchanged protected fixtures, isolated execution | Pass |
| 7 Tests/lint/migrations/build | Actual commands and results above | Pass |
| 8 Report and version stop | This report, completed execution plan; V6 not started | Pass |

## Git, risks and scope

Meaningful commits: `3eb9855` preflight; `6a93598` MCP boundary; `c8a625a` fixture
gates; `2bd3b08` binding; `8845bb1` bound resolution; `ed8cc3a` exact approvals/UI;
`4f0f5b6` publication/recovery; `ed2246b` live object response fix; `1d2339f` actual
publication/recovery/readback evidence. Final completion documentation is committed
separately. No RepoPilot-source remote push or destructive history rewrite.

No required V5 work remains. PRs remain drafts for human review; merging is outside
scope. Frozen profiles only, trusted local single-owner environment, synchronous
requests, bounded reads and the small corpus remain limits. No production auth or
general agent-accuracy claim. Main may move between checks because PR creation lacks
base CAS: stop/reapproval and retained partial objects remain intentional. The MCP
curated PR view omits maintainer-can-modify; false was requested, not independently
read back. Dispatch model prose contains the earlier documented imprecision; tests
and actual diff, not prose, determine verified repair.

No arbitrary repository execution, multi-agent architecture, V6 evaluation platform,
V7 production work, auto-merge or default-branch repair writes were introduced.
**V5 complete; V6 requires a new explicit goal.**
