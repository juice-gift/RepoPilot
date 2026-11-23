# Pre-V8 engineering completion report — 2026-11-03

**Final status: the authorized Phase A–D engineering acceptance is complete within
its approved trusted-local boundary. STOP BEFORE V8.** No new remote GitHub write
or public deployment was authorized or performed. Model accuracy limitations,
unverified semantic outputs and unexecuted hosted CI remain explicitly recorded.

The earlier incomplete assessment at 461d0b7 correctly identified container repair
as missing. The owner subsequently approved the constrained local Sandbox Broker.
That boundary is implemented and has now passed actual container repair, security,
crash/restart and fresh-volume deployment checks. Final application code corresponds
to **ecbc22b**; subsequent closing changes contain evidence and documentation only.

## Acceptance audit

| Phase / criterion | Final result | Evidence / qualification |
| --- | --- | --- |
| A1 application packaging | Complete | Locked API/Web images, pinned base images, separate Broker image, migration gate, nonroot/readonly application runtime; original host development retained |
| A2 configuration | Complete | Explicit deployment core/provider settings; approved policy file plus exact SHA256; immutable test image; private RPC credential; no model-controlled execution settings |
| A3 CI | Defined and locally verified | Ruff, full DB/Docker tests, migrations, frontend build/audit, API/Web/Broker builds and Compose smoke executed locally; GitHub-hosted workflow NOT executed |
| A4 diagnostics | Complete for tested metadata | JSON request IDs, route/status/latency, retrieval/provider/tool/Sandbox outcomes and Broker startup; no raw body/source/SDK exception logging |
| A5 reliability | Complete for authorized failure cases | Provider deadlines, bounded tools/tests, concurrency rejection, durable request identities, process locking, exact retry denial, timeout cleanup and owned orphan recovery |
| A6 deployment | Complete for trusted-local deployment | New Compose volumes/DB, healthy services, deterministic RAG smoke; both Broker and basic modes verified; restart preserves binding/run hashes; backup/restore evidence retained |
| B repository support | Complete within reviewed layouts | Two fixed real Python repositories, root/src package projections, exact baseline source, protected tests and editable paths; original source/Snapshots preserved |
| B safe execution | Complete | Successful repairs, failing baselines, unsupported profiles, path/link/command/oversize denial, stale identities, real timeout and concurrency checks; V4 Golden regression retained |
| C1 integration | Complete | Actual official MCP imports; deterministic real HTTP/API/DB/Broker/Docker repairs for both Issues; separate protected retests match exact final source hashes; durable runs and proposals |
| C2 review/approval | Complete locally | Browser verifies complete diff, baseline, revision, tests, expected commit/branch/PR, digest and limitations; proposals remain awaiting approval |
| C3 publication | Local contracts complete; real writes unauthorized | Existing V5 publication/recovery reused; nested tree/mode and five ambiguous fake-remote recovery cases pass. No new branch, push, commit or Draft PR on GitHub |
| D1 regression | Complete for required local checks | 464 passed /1 optional online MCP skip; migrations, pgvector, build, audit, current images, fresh Compose and frozen evaluation below |
| D2 security | Audit complete | Actual control-plane/sandbox checks, credential scope scan, least mounted authority and owned cleanup; concrete limitations below |
| D3 real-world evaluation | Complete as measured evidence | Scripted and real Qwen records separated; successful earlier runs, current failures, unsupported explanation and unknown cost retained |
| D4 documentation/scope | Complete | README, AGENTS, PROJECT, deployment/security guides, final plan and this report aligned; no V8 work introduced |

The online MCP pytest case remains disabled; it is not counted as PASS. Actual
MCP reads were separately executed through the HTTP import flow. Hosted CI,
independent human semantic review and any new remote publication are not claimed.

## Implementation and architecture

Web -> private API Unix socket -> saved Issue/commit/Snapshot -> existing V1/V2
indexes and V4 bounded read/plan/patch loop -> private API workspace -> authenticated
Broker Unix socket -> independently validated baseline/revision deltas -> private
Broker workspace -> existing isolated Docker executor -> protected tests -> exact
result/source/policy/image identities -> persisted V5 result -> human-review plan.

Only Broker mounts the daemon socket. It runs UID 65534 / socket group 0, network
none, dropped capabilities, readonly root and bounded resources. API/Web contain
no Docker CLI/socket or Broker execution-data mount. Broker receives no database,
model or GitHub credential. API/Web share a distinct private Unix volume; owner
operations still require the exact Origin and actual loopback/private Unix address.
Forwarded IP headers cannot grant owner identity.

Broker accepts one fixed operation and server-approved profiles only. HTTP/model
requests cannot select commands, images, mounts, host paths, Docker arguments,
policy files or dependencies. The operator policy is mounted readonly at the
single fixed `/policy/profiles.json` slot and independently hash-checked. Private
volume ownership/mountpoints, path ancestry, links and resource limits are checked.
Requests are bounded to 8 MB, responses to 32 KB, four connections, a five-second
absolute input deadline and one active job. The 512-entry persistent ledger records
pending identities before effects; exact completed replay is cached and ambiguous
outcomes require operator review. Restart holds an exclusive volume lock and removes
only containers that satisfy this deployment's full ownership/isolation checks.

Child tests retain UID 65534:65534, network none, readonly source/validation mounts,
cap-drop ALL, seccomp/no-new-privileges, CPU/memory/PID limits and fixed timeout /
force-cleanup checks. No third-party repository code ran on the host. No dependency
installer, external service, application credential or daemon socket enters tests.

## Reviewed real repositories and evaluation

| Repository / historical Issue | Immutable commit | Protected baseline -> repaired result |
| --- | --- | --- |
| pallets/itsdangerous #126 | 1a9b8d1f9968eb248bda69f39d373a6330b692ba | 3 failures /5 passes -> 8/8 passes; separate retest passes |
| more-itertools/more-itertools #1336 | 64be96ceb2a6e836f76f069f4a96d2394d59fd0c | 6 failures /3 passes -> 9/9 passes; separate retest passes |

Selection/code/dependency/command review is in [Python review](pre-v8-python-review.md).
Coverage is limited to the audited package-source projections and historical Issue
tests. General Python repository execution and unreviewed dependency installation
remain unsupported. The original 40 KB diff/Golden limits remain; the real 170350-byte
module justified a server-approved 500 KB source-evidence budget under a 1 MB ceiling.

- Final trusted-python scripted harness on ecbc22b: **3/3 passed**, including the
  separate ambiguity case with zero modifications. [JSON](pre-v8-final-trusted-scripted.json).
- Earlier original-Issue Qwen harness on 5963068: two passing repairs and one safe
  owner decision. Exact-output Codex review flags the timestamp interval explanation
  as unsupported. This is not independent human review. [Raw](pre-v8-harness-python-live.json),
  [reviewed](pre-v8-harness-python-live-reviewed.json).
- Actual Web proxy / container API / official MCP / dated Qwen attempts on 0377114:
  **both exhausted the 18-turn limit at revision zero**, produced no repair and no
  publication proposal. Retained without tuning or selective retry in
  [live attempt](pre-v8-container-flow-live-1.json).
- Deterministic provider in a separate API-container test process used actual local
  HTTP routes, DB, Broker and Docker. Both repairs and separately reconstructed
  protected retests pass. The production model provider was not replaced.
  [Full integration evidence](pre-v8-container-scripted-flow.json).
- Earlier task-summary provider failure, max-step failure despite a passing patch,
  malformed new test and evidence-budget refusal remain in their original reports.
  Token/cost fields remain unknown where the provider contract did not retain them.
  These small, differing runs establish no general success rate or improvement.

Current container proposals: `e1acb0e716fe4d059c2f9231813a2063` and
`6107aafaa53b40bcb0b770af598bcf63`, both **awaiting_approval**. The existing
private-owner/current-main publication gate additionally refuses these public
historical upstream targets. No approval checkbox or publish action was used.
[Browser review](pre-v8-container-review-browser.jpg).

## Validation actually executed

Full pytest enables RUN_DATABASE_TESTS=1, RUN_SANDBOX_TESTS=1 and
RUN_TRUSTED_PYTHON_TESTS=1. Source code: ecbc22b.

| Command/check | Result |
| --- | --- |
| `uv run pytest -q` | **464 passed, 1 skipped, 1 existing Starlette/AnyIO deprecation warning**, 178.28s; [output](pre-v8-final-pytest.txt) |
| `uv run ruff check src tests migrations` | Passed |
| `uv run alembic current` / `uv run alembic check` | 0008_github_publications head; no new upgrade operations |
| Disposable migration test in full suite | Clean replay, pgvector, sentinel preservation, downgrade/upgrade and drift checks passed; only owned temporary DB removed |
| `npm run build` / `npm audit --audit-level=high` | TypeScript/Vite build passed; zero audit findings; no separate frontend lint/test scripts configured |
| Current API/Web/Broker Docker builds | Passed; image IDs and actual mount/network/health metadata in [deployment evidence](pre-v8-final-deployment-check.json) |
| Fresh `repopilot-broker-clean` Compose project | New DB/data/IPC volumes, clean migration and healthy services; Broker mode and basic mode both verified |
| `scripts/compose_smoke.py` on 8083 | Both modes: repo/snapshot 1, 19 chunks, one deterministic citation; [Broker-mode smoke](pre-v8-final-clean-compose-smoke.json), [basic-mode smoke](pre-v8-final-basic-compose-smoke.json) |
| Independent rebuilt-image runtime policy | Both repairs/retests pass with reviewed image f7e01c83...ee81af8; historical corpus unchanged; [evidence](pre-v8-final-clean-policy-probe.json) |
| Current Broker Docker security probe | Authentication/profile/path/command/oversize/replay/conflict/concurrency/real 20s timeout/cleanup passed; [evidence](pre-v8-broker-final-probe.json) |
| Real Linux transport/path checks | Duplicate framing/auth, chunked/Expect/malformed JSON denied; input deadline, actual symlink denial, socket modes and unavailable-Broker no-fallback passed; [evidence](pre-v8-broker-final-transport-probe.json) |
| Broker force-kill/restart | Second process denied; verified owned orphan/workspace cleaned; pending identity retained and exact retry returns 409; [evidence](pre-v8-broker-final-restart-probe.json) |
| App restart/persistence | All services healthy; two bindings/four runs and exact hashes preserved; API has private Unix listener and no Docker CLI; [evidence](pre-v8-final-deployment-check.json) |
| Final frozen V6 CLI, original 17 cases | **12 passed /5 semantic outputs unverified**, no failed cases after configuration correction; [report](pre-v8-final-v6-frozen-regression.json) |
| First closing frozen CLI attempt | Three resolution infrastructure errors because the image setting was omitted; retained [initial report](pre-v8-final-v6-initial-missing-image.json), then rerun with explicit frozen image |
| Backup/restore earlier in this Goal | Restored into NEW verification DB; 17 Snapshot rows and matching aggregate 387b77cc39bee8ca0267329d514eec1d; original volume retained |
| Credential and scope audit | [Final scan](pre-v8-final-security-scan.json); no provider/Broker/new-deployment credential matches, log matches or image-config matches; existing development placeholder noted below |
| Git diff whitespace audit | Implementation diff clean; verbatim owner Goal retains intentional Markdown two-space line breaks |
| GitHub-hosted workflow | NOT EXECUTED; local equivalents do not establish hosted CI PASS |

The clean verification project is stopped with volumes retained. The original
`repopilot` stack is retained. The accepted local review stack on localhost:8082
remains available; its exact private configuration files stay outside Git. No owned
Sandbox test container remains. No important user data or Git history was removed.

## Changed files, dependencies and Git

Important files: API/Web Dockerfiles and nginx upstreams; `compose.app.yaml` and
`compose.broker.yaml`; `.dockerignore`, `.env.example`, CI; Settings/diagnostics;
resolution workspace/profile/patch/Sandbox/Broker modules; GitHub binding, trees,
resolution/proposals/publication contracts and catalog API; React review/types;
trusted evaluation adapter/graders/tests; reviewed licensed corpus; deployment,
security, plan and machine-readable evidence. No database schema/migration changed.

No new Python package or frontend package family was added. npm lock entries for
Vite 7.3.7/source-map-js 1.2.2 address the observed advisories. uv 0.11.8 is build
tooling; Node/Nginx support the requested application containers. Broker alone adds
the official Docker CLI binary pinned to image digest
3f4743208d2338c934d7b8bcfbe1bb54c0b2355c510ad5e0f31c0c4a54bd704e.

Local milestone commits: e864545 authorization; aeb0e69 lock security; bcd7b03
packaging/CI/config; 544f741 diagnostics/deadlines; b7d5f82 reviewed Python profiles;
8b97521 binding/repair/proposals; 29fd645 UI/recovery; 270e8d7 frozen evaluation;
5963068 real corpus harness; 9a9286b live evidence/runtime policy; 461d0b7 incomplete
audit; 47807f2 owner Broker approval; 82f1664 Broker validation/ledger;
0377114 authenticated deployment; ecbc22b real HTTP/security/failure evidence.
Closing evidence/documentation is committed separately. No push or remote rewrite.

## Known limitations, unexecuted work and risks

- Real Qwen behavior remains unreliable: current container attempts failed safely;
  earlier success includes an unsupported explanation. Five frozen semantic outputs
  still need independent review. Unknown outputs are not counted as success.
- Hosted CI is unexecuted. New actual GitHub publication/public hosting remain
  unauthorized. Current historical public targets are not publishable under V5.
- The original development DB still uses the public template credential. Its three
  matching template/test files already existed at 40ccf6f; no value is printed here.
  New acceptance deployments use generated private credentials. Existing DB
  credentials were not changed; retain the trusted-local, loopback-only boundary.
- Broker has local Docker authority despite its nonroot Unix identity. A compromised
  Broker/daemon/host remains a high-impact risk. This is a trusted single-owner
  system, with no hostile multi-tenant or public-service security claim.
- Broker runtime is actually verified on Windows Docker Desktop's Linux engine with
  socket group 0. Other socket ownership/platform configurations are unverified and
  have no automatic root/privileged fallback. Ledger exhaustion/unexpected orphan
  metadata requires operator maintenance; ambiguous effects are never blindly rerun.
- Protected Issue tests provide bounded coverage; arbitrary projects, installers,
  external services and general correctness are not supported guarantees. Existing
  Starlette/AnyIO deprecation warning remains non-blocking.

## Final scope and stop boundary

All mandatory engineering checks within the authorized trusted-local A–D scope
have evidence above. No unresolved blocking engineering defect remains. Unverified
model semantics, hosted CI and unauthorized remote effects are explicitly separated
from implemented/validated functionality; acceptance standards were not relaxed.
No new model tuning was performed to erase the failed closing attempts.

No V8 presentation/packaging, public demo, public deployment, new Agent framework,
multi-agent system, queue, Redis, Kubernetes or unrelated refactor was introduced.
**Engineering prerequisites are verified within the stated local scope. V8 is not
authorized. Stop here; the owner decides any subsequent Goal.**