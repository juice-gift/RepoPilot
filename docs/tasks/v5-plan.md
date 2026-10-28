# RepoPilot V5 Execution Plan

## Goal and current state

Implement the [authorized V5 goal](../goals/v5-mcp-github.md).
Authorized 2026-10-27; branch `codex/v5-mcp-github`, clean-main baseline
`0308e8ab588d8d2a15ad960325e1d062f330eb45`. Remote `origin/main` was independently
checked with `git ls-remote` and matched.
**M0–M2 complete. Fixture preparation blocker resolved; M3 next.**
Owner resumed local engineering on 2026-10-28, selected juice-gift as test repository
owner and requested a private fixture preparation plan. Owner subsequently confirmed
juice-gift/repopilot-v5-sandbox, Issues 1/2/3 and local Token configuration. The
initial mismatches and permission failures are retained below. Current verified
baseline is b4279c8b4d862817e6778caa5f87da91d29ed2b7; V5 remains incomplete.

## Milestones

| Milestone | Deliverable and required verification | State |
| --- | --- | --- |
| M0 | Goal/plan, V4 regressions, live DB/Docker, official research, capability gaps | Complete |
| M1 | Explicit bounded MCP Client, discovery/schema checks, allowlisted reads, actual official-server read | Complete: actual identity/repository/commit/file/Issue/PR-list reads verified |
| M2 | Canonical repository/Issue/commit/Snapshot binding, bounded source import, migrations and integrity checks | Complete: real MCP→PostgreSQL import and idempotency verified |
| M3 | Approved controlled GitHub fixture → existing V4 repair → persisted diff/results/test evidence | Next |
| M4 | Reviewable exact publication proposal, explicit human approval, server permission gates, minimal React integration | Pending |
| M5 | MCP branch/commit/PR publication, stale-base guards, recovery/idempotency, live approved write evidence | Pending exact proposal approval |
| M6 | Full V1–V4 regression, live acceptance audit, Completion Report, V5/V6 stop | Pending |

Each milestone requires relevant tests, self-review and a meaningful commit.
No milestone may use simulated integration as proof of actual remote success.

## Preflight evidence (2026-10-27)

Read AGENTS.md, PROJECT.md, V4 goal/plan and
[V4 completion report](../evaluation/v4-issue-resolution-status.md). Inspected
resolution profiles/service/tools/contracts/patch, ingestion service, DB Snapshot
model, config, tests, dependency manifests and relevant Git history.

| Command/check actually executed | Result |
| --- | --- |
| `git status --short`, branch/log and remote main check | Clean main; local/remote baseline matched |
| `uv run pytest -q` from apps/api | 238 passed, 24 opt-in skips; existing AnyIO deprecation warning |
| `uv run ruff check src tests migrations` from apps/api | Passed |
| `npm run build` from apps/web | Passed TypeScript and Vite production build |
| `docker info --format '{{.OSType}}'`, `docker compose ps`, image listing | Initial failure: Docker Desktop Linux Engine named pipe absent |
| Initial `uv run alembic current` and `uv run alembic check` | Failed: PostgreSQL connection timeout while Docker unavailable |
| Hidden Docker Desktop start, `docker compose up -d database`, runtime/image recheck | Recovered; Linux engine, healthy existing database, prepared V4 immutable image available |
| Repeated `uv run alembic current` and `uv run alembic check` | Passed: 0005_structural_index (head); no new upgrade operations |
| `RUN_DATABASE_TESTS=1 RUN_SANDBOX_TESTS=1 uv run pytest -q` (PowerShell environment variables) | 262 passed, no skips; includes real isolation tests, DB/pgvector/API checks and disposable migration replay |
| Environment and project .env GitHub/MCP variable names (no values printed) | No GitHub MCP credential setting found; `GH_PAGER` is not a credential |

Docker/DB availability was restored without changing application code, data or
configuration. Sandbox image: `sha256:71aebb88109cbb7c2eb535ef4321a4b9d23b886c0c14625bafaeb9e78b5fea5f`.
Initial failures remain recorded above. The first V1 CLI command also failed
because PYTHONPATH was missing; corrected all subsequent CLI invocations with
`$env:PYTHONPATH = 'src'`. This does not affect pytest's configured pythonpath.

Frozen CLI revalidation (commands run from apps/api):

- `uv run python -m repopilot.evaluation.runner --strategy vector --top-k 5`:
  Hit@1/3/5 = .75/.875/1, MRR@5 = .8375; [report](../evaluation/v5-preflight-v1-vector.json).
- Same command with `--strategy hybrid`: metrics remain 1;
  [report](../evaluation/v5-preflight-v1-hybrid.json).
- `uv run python -m repopilot.evaluation.structural --output ../../docs/evaluation/v5-preflight-v2-structure.json`:
  definitions 16/16, imports 5/5, targets 8/8, occurrence/status 21/21;
  [report](../evaluation/v5-preflight-v2-structure.json).
- `uv run python -m repopilot.evaluation.agent --output ../../docs/evaluation/v5-preflight-v3-scripted.json`:
  three completed scripted investigations with expected evidence;
  [report](../evaluation/v5-preflight-v3-scripted.json). This does not measure LLM accuracy.
- With RESOLUTION_SANDBOX_IMAGE set to the inspected immutable image ID,
  `uv run python -m repopilot.evaluation.resolution --mode scripted --output ../../docs/evaluation/v5-preflight-v4-scripted.json`:
  fee-days and dispatch-preconditions verified repairs; ambiguous-cap returned
  needs_owner_decision; all three frozen Golden conditions passed;
  [report](../evaluation/v5-preflight-v4-scripted.json). Actual DB/Docker execution,
  scripted model protocol only; this is not actual MCP/GitHub evidence.

No external Qwen rerun has been performed in V5 preflight; historical V4 real-model
evidence remains in its completion report, not claimed as a new V5 measurement.

## M0 review and scope

Changes are limited to this goal/plan, current-stage notices in AGENTS.md,
PROJECT.md/README and five actual regression reports. No application code,
architecture, dependency, schema, migration, credential or frozen fixture changed.
The initial main/remote baseline was clean; engineering work is isolated on the
new V5 branch. No remote writes, fixture/Issue creation, push, PR or merge occurred.
V1–V4 limits and historical failures remain intact. `git diff --check` passed.
Remaining risk: real MCP compatibility and remote publication safety are still
unimplemented/unverified; passing regressions does not imply V5 acceptance.

2026-10-28 resumption: owner confirmed Docker is running; completed live results
above already establish this. All three V4 reports confirm unchanged original and
Snapshot plus workspace cleanup; final Docker inventory has only the database
container. No redundant regression rerun is needed for this documentation-only
checkpoint. Final evidence JSON parsing and scoped credential-pattern scan passed.
The first audit glob used PowerShell-style expansion unsupported by rg; reran with
rg's own `-g` filter. This affected the audit command only, not test results.

## Official-source research

Consulted 2026-10-27; these are observations, not interoperability claims:

- [Current specification](https://modelcontextprotocol.io/specification/latest)
  resolves to 2026-07-28. [Transport rules](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
  describe per-request metadata and compatibility with handshake-era servers.
- [Official Python SDK](https://github.com/modelcontextprotocol/python-sdk),
  [client docs](https://py.sdk.modelcontextprotocol.io/client/) and
  [protocol versions](https://py.sdk.modelcontextprotocol.io/protocol-versions/):
  current stable documentation is v2, with `Client`, paginated `list_tools` and
  `call_tool`. Auto mode probes discovery and supports legacy handshake fallback.
  PyPI metadata queried directly reports `mcp==2.3.0` (Python >=3.10). Select and
  lock a release and inspect its installed API during M1; record the actual
  protocol rather than assuming latest support. No dependency has been added yet.
- [Official GitHub MCP Server](https://github.com/github/github-mcp-server) and
  [configuration](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md):
  hosted endpoint `https://api.githubcopilot.com/mcp/`, PAT authentication,
  tool selection and read-only headers are documented. Lockdown is a content
  filter, not an authorization boundary. Start with a separate read-only client.
- [MCP security guidance](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)
  covers credential, confused-deputy and endpoint trust risks. No arbitrary
  caller-supplied MCP endpoints or automatic server instruction execution.

Implementation must examine discovered tools and actual schemas. In particular,
the documented high-level `push_files` accepts a branch but no expected head SHA;
it must not be assumed to provide atomic baseline protection. During M1/M5 inspect
official Git tools for exact-parent commit and safe ref creation capabilities.
If the required publication guarantee cannot be enforced, escalate before writes;
do not substitute a pre-read alone for a concurrency guard.

## M1 implementation and current evidence (2026-10-28)

- `github/client.py`: explicit official SDK v2 connection/discovery and allowlisted
  reads. Fixed HTTPS endpoint and transport guard prevent credential-bearing
  redirects to other paths/hosts. Explicit read-only server header plus independent
  local repository/operation/path/SHA/argument-schema gates; no write capability.
  Responses/schema/pages/calls/time are bounded; resource URLs are not followed.
- Settings loads root `.env` or overriding process environment. GITHUB_MCP_TOKEN
  uses SecretStr and is excluded from repr/export. Validation messages hide inputs.
  Mapping: in-memory Bearer header for remote Server; local Server's separate
  GITHUB_PERSONAL_ACCESS_TOKEN is not set. Existing Sandbox environment allowlist
  excludes both. SDK/network logs are suppressed within the MCP async context;
  only application-owned failure codes cross the boundary.
- `github/probe.py`: real connection/discovery/get_me identity check, safe metadata
  only, no raw tool result or Token. CLI actual attempt returned credential_missing
  before opening transport. This is **unverified**, not a successful connection.
- Added local protocol/policy tests plus a separately opted-in live identity test.
  In-process and local ASGI HTTP tests use the actual SDK but are not GitHub evidence.
- Runtime dependencies: mcp==2.3.0 for protocol; jsonschema for discovered argument
  schemas; anyio for bounded async cancellation/timeouts. Existing httpx2 moved
  from dev to runtime for explicit authenticated HTTP transport. uv.lock updated.
- [Private fixture preparation plan](v5-github-fixture-preparation.md) contains
  exact five-file root/hashes, three Issue titles/bodies, initial PAT read scopes,
  proposed repository name and information the owner must return. No fixture,
  Issue, branch, commit or PR was created remotely. Frozen V4 files are unchanged.

Actual checks after these changes:

| Check | Result |
| --- | --- |
| `uv run pytest -q tests/test_github_mcp.py tests/test_config.py` | 26 passed |
| Full suite with RUN_DATABASE_TESTS=1 and RUN_SANDBOX_TESTS=1 | 282 passed / 1 live-MCP opt-in skip; existing AnyIO warning |
| Ruff src/tests/migrations | Passed |
| Alembic current/check | Head 0005; no new operations |
| npm run build | Passed |
| `PYTHONPATH=src uv run python -m repopilot.github.probe --expected-login juice-gift` (PowerShell env assignment) | Exit 1, credential_missing; no real MCP connection made |

Initial SDK inspection used the wrong MCPServer import; corrected to mcp.server.
Initial Ruff broad-exception findings were resolved with narrowly documented
third-party trust-boundary suppression; no raw failure logging was added.
Self-review: no remote writes, no model-controlled authority, no V4 profile/sandbox
relaxation, no database migration/architecture change or later-version capability.

## Verified V4 → GitHub capability gaps

| Existing behavior | V5 responsibility |
| --- | --- |
| Ingestion reads an allowed local path; saved source_revision is None | Canonical remote identity and verified commit binding, not caller-asserted SHA |
| Snapshots deduplicate by repository/content hash | Preserve multiple commit bindings when identical source content appears at different commits |
| Scanner filters files; Snapshot is not a full Git tree | Preserve full remote tree and modify only approved existing source paths |
| Profiles require exact frozen source hashes and protected independent tests | Controlled remote fixture must match approved profile; arbitrary repository stays non-executable |
| V4 request allows only three case profiles and bounded issue text | Bind imported Issue to selected profile, immutable commit and untrusted bounded content |
| Owned temporary workspace is cleaned after result return | Persist authoritative result/patch/test evidence before publication; never trust a browser-supplied verified status |
| ResolutionResult includes changed original/modified source and revision-bound tests | Bind approval and remote commit to the exact stored verified result and original base |
| No product-agent Git, remote approvals or durable publication state | Add minimal PostgreSQL-backed proposal/outcome records with migrations; no job platform |

Keep V1 indexing and V3 investigation independent. Do not relax frozen V4
manifest/profile permissions to accommodate unrelated GitHub files or execute
remote setup scripts. No multi-agent work is authorized.

## Actual MCP read-only audit and new blocker (2026-10-28)

Owner selected `juice-gift/repopilot-v5-sandbox`, Issues 1/2/3 and supplied SHA
`6a9359843eb56ecbd3a569e63c93a2d747ac64c1`. This is a fresh audit after resumption;
the previous credential blocker is resolved. Reads were explicitly limited to
that repository using the Settings constructor allowlist; no .env value was
printed or modified. No connector/REST substitute was used for this evidence.

[Actual report](../evaluation/v5-github-readonly-audit.json), observed
2026-10-28 12:52 Asia/Shanghai:

- Official remote MCP Server, SDK 2.3.0, negotiated protocol 2026-07-28.
  get_me matches juice-gift. Repository id 1436602856, private, default main,
  reported pull permission true; successful scoped reads confirm read access.
  Role flags are not proof of PAT write scopes; no write authorization or test.
- Actual main SHA: `8728cea64153aa7476c8c003b47dc24402d429b2`, different from the
  supplied SHA (which is the local RepoPilot development commit).
- At that exact remote SHA the root contains only README.md. Its embedded source
  is `# repopilot-v5-sandbox`, not the frozen README. auth.py, fees.py, policy.py
  and workflow.py are missing. All source comparisons fail. No code was executed.
- Issues 1/2/3 exist with the expected case titles, but MCP responses contain no
  body. None matches its frozen contract. The observed response uses an explicit
  issue/method wrapper; parsing validates the exact repository URL and number.
- First PR list page is empty. A specific PR read remains unverified until one
  exists after separately approved publication; no artificial PR was created.
- Local frozen manifest and independent test integrity pass. As specified by the
  preparation plan, independent tests stay in RepoPilot, not in the remote repo.

Added only the required exact-repository search tool for metadata. Its query is
constructed and independently checked against the local allowlist; broader search
cannot expand access. Added a read-only fixture auditor: immutable resource URI,
source SHA256, issue contract and baseline checks. A failed gate produces a report,
never a partial executable workspace or silently substituted baseline. No M2
Snapshot/import/repair was started because the owner's preparation gate failed.

Validation: Ruff passed; focused config/MCP/audit tests **32 passed**, including
the opted-in actual official-server identity test. The fixture auditor itself
performed actual remote reads and returned blocked_fixture_mismatch; this failure
is retained, not presented as successful fixture integration. Full regression
with RUN_DATABASE_TESTS=1, RUN_SANDBOX_TESTS=1 and RUN_GITHUB_MCP_TESTS=1:
**288 passed, no skips**, including actual identity, database, migration replay and
Docker isolation tests. Existing AnyIO deprecation warning remains. No new
dependency/schema/migration/UI change; prior frontend build remains applicable.

Generated a local upload kit in an OS temporary directory: ZIP contains exactly
five original source files (each hash rechecked); separate text file contains all
three frozen Issue bodies. No protected validation tests or credentials in the ZIP.
Owner must extract/upload the five files, replace the initial README, fill Issue
bodies and supply the resulting main SHA. This does not authorize remote writes.

## Blockers and resumption

Latest resumption: owner reported Issues write permission configured, spelling the
repo repopilot-v5-test. Continued only the previously authorized sandbox, without
expanding scope. The helper successfully updated and read back all three Issue
bodies; [final MCP audit](../evaluation/v5-fixture-final-audit.json) passes all gates.
The default-branch fixture commit remains b4279c8b4d862817e6778caa5f87da91d29ed2b7.
This completes the explicit preparation authorization; future repair writes remain
subject to separate approval. The historical 403 below is resolved, not erased.

M2 implementation: github/binding.py imports only exact verified frozen source
directly from immutable MCP resource URIs, rechecks main before persistence, and
atomically saves SnapshotFiles and three Issue/commit bindings. No host checkout,
clone or execution occurs. A stable github:// repository identity uses GitHub's
numeric repository id. Migration 0006 adds github_issue_snapshots. The existing
Snapshot content identity is unchanged; source_revision remains unset rather than
misrepresenting multiple commits with identical filtered bytes. The association
table retains every Issue/commit binding separately. Permission/Issue content is
never accepted from an HTTP/model-supplied audit report; persistence is internal.

[Actual MCP/DB import evidence](../evaluation/v5-github-snapshot-binding.json):
local Repository 285, Snapshot 414, three bindings 13/14/15, five saved source files;
repeating persistence preserves all binding ids. Tests cover equal-byte/different
commit provenance, corrupted saved source, conflicting binding, invalid profile
and complete transaction rollback. Migrations apply and clean disposable replay
passes. Final checks: full DB/Docker/actual-MCP suite **290 passed, no skips**;
Ruff, Alembic current/check (0006, no changes), and frontend build passed.
Initial Docker/database connection failed; local Docker was restored before the
passing checks. Initial Ruff import/noqa issues were fixed. No new dependency,
execution permission relaxation or product remote-write capability was introduced.

Owner explicitly authorized fixture-only writes on 2026-10-28: exactly five frozen
source files on the private sandbox main, and original bodies of Issues 1/2/3.
This is a one-time setup exception, not a product default-branch write capability.
GitHub connector returned 404 for the private repo, so preparation used a separate
operator MCP session with fixed push_files/issue_write arguments. Product read-only
client and its allowlist were not broadened.

Files committed once: original main 8728cea64153aa7476c8c003b47dc24402d429b2 →
**b4279c8b4d862817e6778caa5f87da91d29ed2b7**. Independent read-only MCP audit verifies
private repo, identity, current main, exact root paths and all five SHA256 hashes.
Protected tests stayed local and their manifest integrity passed.
[Preparation outcome](../evaluation/v5-fixture-preparation.json) and
[post-write read-only audit](../evaluation/v5-fixture-prepared-audit.json).

Issue #1 update failed with actual GitHub PATCH 403, Resource not accessible by
personal access token. Readback confirmed no change; a reconciled retry produced
the same explicit permission error. No Issue body updates succeeded; no attempts
were made to write #2/#3 after this diagnosis. No repair branch/commit/PR, merge,
or remote RepoPilot-source write occurred. No Token was printed or persisted.
Initial preparation inspection incorrectly expected a tree in curated get_commit
output; it failed before writes and was corrected without using invented metadata.

Fallback helper: docs/tasks/v5-update-issue-bodies.py. It changes only bodies of
the three fixed Issues, only after verifying this exact baseline and frozen source;
no file push or PR tool exists in it. Default invocation is read-only. After
granting the locally configured PAT Issues: Read and write on this repository,
from apps/api run `$env:PYTHONPATH='src'`, then
`uv run python ../../docs/tasks/v5-update-issue-bodies.py --apply`.
Alternatively manually paste the three original manifest descriptions into Issue
bodies in GitHub. The five files do not need uploading again. Resume only after
the final source+Issue audit passes; no later repair-publication write is approved.
Helper Ruff and its actual default read-only run passed (all source/baseline gates
true, Issue contract gate false). Its --apply write path remains permission-blocked;
it is not presented as successfully executed. Application code/dependencies/schema
and frozen fixtures did not change, so the prior 288-pass regression is retained
as historical evidence, not claimed as a newly rerun suite.

- Resolved: locally configured credential and real official MCP connection/identity.
- Resolved: Issues permissions, three original bodies, frozen source and immutable SHA.
- Remaining implementation: M3 controlled repair persistence, M4 proposal/UI and
  permission gates, M5 approved publication, M6 final acceptance.
- Required before actual writes: exact publication proposal and human approval.
  The version authorization alone is not permission to create remote fixtures,
  issues, branches, commits or PRs.
- Docker/DB startup and full live regression are now resolved as recorded above.

Do not ask for raw tokens in chat. Credentials should be configured locally in
ignored environment configuration with minimal repository scope. Implemented M1
setting: `GITHUB_MCP_TOKEN`; begin with read-only Contents/Issues/Pull requests
access to the controlled repository. Empty GITHUB_MCP_ALLOWED_REPOSITORIES denies
repository reads while permitting discovery/identity. Scope reads only to the
owner-confirmed repository; remote text cannot add another repository to scope.
Fixture preparation no longer blocks development. Preserve exact identity and
profile checks; do not guess Issue intent or relax a frozen profile. V5 is incomplete;
do not issue a Completion Report that implies acceptance. M2–M6,
commit/Snapshot binding, positive fixture integration and individual PR live
reading remain outstanding; successful raw reads alone do not satisfy them.
