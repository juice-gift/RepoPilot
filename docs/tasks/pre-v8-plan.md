# Pre-V8 execution plan — 2026-11-03

Active authorization: [Goal](../goals/pre-v8-engineering.md). Branch:
`codex/pre-v8-engineering`; baseline 40ccf6f. Stop before V8. No remote writes or
public hosting authorized. Owner separately approved selecting/reviewing two small
public Python repositories and offline Docker tests; no further selection approval.

| Milestone | State | Evidence |
| --- | --- | --- |
| M0 Preflight | Complete | clean baseline, read-only fetch origin/main 5316cf8, existing V4–V6 inspected, 373-pass live baseline |
| A1 Packaging/config | Implemented, partial deployment acceptance | locked API/Web images, migration gate, loopback Compose; container repair unavailable |
| A2 Diagnostics/reliability | Tested paths complete | JSON correlation/latency, safe failures, bounded providers/Sandbox, cleanup and exact publication recovery |
| A3 CI/deployment | Local execution verified | fresh stack/new volume/start/restart/smoke/restore; hosted CI NOT executed |
| B1 Trusted profiles | Complete within limited layouts | operator registry + exact SHA256, immutable sources/image/tests, root/src, no shell/install options |
| B2 Real repositories | Verified | ItsDangerous #126 and more-itertools #1336, success/failure/refusal/stale/path boundaries, original Golden regressions |
| C Integration | Local/read-only acceptance verified | actual official MCP bindings; real DB/Docker repairs; exact awaiting-review plans; nested fake-remote recovery; UI |
| D Regression/evaluation/security/docs | Evidence saved; full acceptance open | 414 passed /1 disabled online MCP skip; real harness; security review; decision below |

## Current work / remaining acceptance

Full Goal is NOT complete. Owner approved the constrained local Broker on
2026-11-03. Its private authenticated Unix transport, independent fixed-profile
validation, private volume mapping, nonroot/network-none execution, ledger and
process locking are implemented. Real container API -> Broker -> Docker probes
repair both approved repositories and independently pass 8/8 and 9/9 tests.
Crash/restart removes only verified owned orphan resources and denies ambiguous
request replay. Web -> API uses a separate private Unix volume; exact Origin
checks remain mandatory, and forwarded network headers are not trusted.
Complete the actual Web/HTTP Issue workflow, transport adversarial checks, final
full regression and security/docs audit before accepting the Goal.
Hosted CI is unexecuted and cannot be called GitHub PASS. No new real GitHub write
is authorized; public historical upstream plans additionally fail the unchanged
private-owner/current-main publication gate. After the execution-boundary decision:
implement authorized choice, test actual container repair if applicable, review
all acceptance again, update final report and stop before V8.

## Latest measured validation

- Final full `uv run pytest -q`, DB/Sandbox/trusted flags enabled: **414 passed /
  1 disabled online MCP skip**, 171.18s, code 9a9286b. Starlette/AnyIO warning remains.
- Ruff passed; Alembic 0008 head/check no drift; clean replay/pgvector/sentinel and
  reverse/replay included in full suite. npm TypeScript/Vite build passed.
- Actual new `repopilot-pre-v8-acceptance` project, NEW volume, loopback 55432/8081:
  images/clean migration/health passed, smoke repo/snapshot 1, 19 chunks, one
  deterministic citation; API/Web restart preserved IDs/content. Test stack stopped
  without deleting its volume. Original stack/volume retained.
- Quiescent backup restored into NEW verification DB: 17 snapshot rows, both row
  aggregate hashes 387b77cc39bee8ca0267329d514eec1d. No original data deletion.
- Rebuilt-image runtime policy simulation: 30 passed (actual DB/Docker + fake
  publication); historical policy/evidence identities remain immutable.
- Actual official MCP trusted imports: bindings 2138/2140, snapshots 1566/1568;
  zero remote writes. Deterministic bound repairs generate proposals
  fc73598c6f744186b2d7af63f802486c / f09d2f51abce4e078f3bc86e86903296 awaiting approval.
- Nested fake-remote tree/commit/branch/PR timeout recovery: 5 cases passed, no
  duplicate effects. UI showed approved profiles, exact diff/test revision/plan
  and limitations; no approval checkbox or publication action used.
- V6 frozen 17-task CLI regression preserved; five semantic outputs remain unverified.
- Current `trusted-python` corpus (5963068): scripted 3/3; actual dated Qwen 3/3,
  two repairs (8/9 independent final tests) and one zero-change owner decision.
  Codex exact-output review flags unsupported timestamp-interval prose in the first
  answer; task success stays separate. Tokens/cost unavailable. Earlier summary-
  input provider failure/max-step failure and initial evaluator/budget errors remain
  distinct, preserved evidence. No general accuracy/improvement claim.
- Configured key/token scans of pre-v8 reports: zero matches. No owned Sandbox
  container remains. Task-owned API 8001/Vite 5174 stopped after browser verification.

## Decisions, commits and evidence

Full details, commands, requirements and remaining limits:
[acceptance report](../evaluation/pre-v8-engineering-completion.md),
[security review](../evaluation/pre-v8-security-review.md),
[Python source/execution review](../evaluation/pre-v8-python-review.md),
[deployment](../deployment.md), [trusted Python](../trusted-python.md).

No new package/schema/framework/queue/service introduced. npm lock-only security
patches applied. Larger real module justified explicit bounded source-evidence
budget (500KB profile, 1MB ceiling); Golden default/diff limits retained. App images
never received daemon access. New broker is design-only pending permission.

Local milestone commits: e864545, aeb0e69, bcd7b03, 544f741, b7d5f82, 8b97521,
29fd645, 270e8d7, 5963068, 9a9286b. Detailed historical progression is preserved in
Git and raw reports; no history rewrite, push, PR, merge or public deployment.

## Broker authorization received — 2026-11-03

Owner approved the independent local Broker with six mandatory security constraints;
host execution of third-party tests is NOT an alternative. New work: Bk1 protocol/
independent validation, Bk2 private authenticated Unix transport/admission/dedupe,
Bk3 nonroot no-network Compose broker and owned-volume path mapping, Bk4 actual
container API/Web repair plus adversarial/concurrency/timeout/restart regression,
then repeat required final B/C/D acceptance. No new remote writes/public hosting.
Further host privilege expansion or failing isolation remains a stop condition.

Bk1 implemented: request schema accepts only profile identity, baseline and bounded
revision deltas; commands/images/mounts/host paths/Docker options are forbidden.
Broker independently checks exact approved baseline, policy hash, every changed
path, revision count, source/file budgets and cumulative diff before materializing.
Workspace keeps private immutable delta copies; Sandbox results include actual
source identity. Runtime core provides single-job admission, persisted pre-effect
request markers, exact cached-result replay, conflict/ambiguous-outcome denial and
private workspace cleanup. Execution adapters remain internal and server-selected.
Protocol/workspace/patch focus: 43 passed. Runtime/protocol focus: 40 passed /6
non-enabled Docker skips; actual Docker follow-up completed with 36 passed.
Docker Desktop probe confirmed UID 65534 / group 0 can use its group-owned Unix
socket without root, privileged mode, extra capabilities or TCP exposure. Official
Docker CLI image 29.7.2 pulled and pinned at digest
3f4743208d2338c934d7b8bcfbe1bb54c0b2355c510ad5e0f31c0c4a54bd704e.
Next: authenticated Unix HTTP transport, strict owned-volume startup validation,
process locking/orphan cleanup, API executor adapter and Compose wiring, then real
container repair and the required adversarial/concurrent/timeout tests. No daemon
socket is mounted in API/Web; only the approved dedicated Broker receives it.
No new remote writes.

### Bk2 — private Broker transport/deployment

Implemented authenticated Unix HTTP, 8 MB body/32 KB response bounds, bounded
connections and absolute input deadline, fixed server-owned image/profile/path
selection, private Compose volume metadata mapping, Linux process lock, orphan
verification/cleanup, persistent exact replay and API client evidence validation.
API/Web have no Docker CLI/socket; separate private Unix API/Web transport keeps
the existing exact Origin owner gate without trusting forwarded IP headers.
Targeted tests: 64 passed, then 8 owner-transport cases after checking actual
Uvicorn Unix address metadata. Actual two-repository Docker probe and force-kill/
restart evidence saved in `docs/evaluation/pre-v8-broker-*.json`. Both repairs and
independent rechecks pass, baseline failures retained, 20-second infinite-loop
timeout cleaned. Full HTTP/model workflow and final complete regression remain.

### Bk3 — HTTP integration and final hardening

Actual Web proxy/Unix API/MCP/Qwen attempts on 0377114 imported both originals but
both exhausted 18 turns at revision zero. Retained in
`pre-v8-container-flow-live-1.json`; no selective retry or success claim. Separate
scripted-provider test process inside API used actual loopback HTTP routes, real
DB, Broker and Docker: both repairs verified; separately rerun protected tests
match the exact result source hashes. Both proposals remain awaiting approval.
Browser review verified full diff/identity and disabled unapproved actions; image
saved. Production provider configuration was not changed to a scripted mode.

Adversarial Linux transport checks reject duplicate framing/authentication,
chunked/Expect requests and malformed JSON, enforce a five-second absolute input
deadline, verify 0600 socket/0700 directory and actual inside/outside symlink denial.
Final startup hardening independently verifies BOTH local-volume labels/mountpoints,
Broker resource limits and directory ownership/modes. A single fixed readonly
operator-policy mount supports rebuilt reviewed image IDs without rewriting the
historical corpus; requests still cannot name policy paths or execution options.
CI now also builds the Broker image; hosted execution remains unperformed.
Final complete regression, current-image probes/restart and documentation audit next.
