# RepoPilot V5 Execution Plan

## Goal and current state

Implement the [authorized V5 goal](../goals/v5-mcp-github.md).
Authorized 2026-10-27; branch `codex/v5-mcp-github`, clean-main baseline
`0308e8ab588d8d2a15ad960325e1d062f330eb45`. Remote `origin/main` was independently
checked with `git ls-remote` and matched.
**M0 complete. M1 local implementation tested; actual MCP verification awaits Token.**
Owner resumed local engineering on 2026-10-28, selected juice-gift as test repository
owner and requested a private fixture preparation plan. No repository name/Issue
has yet been confirmed; V5 remains incomplete.

## Milestones

| Milestone | Deliverable and required verification | State |
| --- | --- | --- |
| M0 | Goal/plan, V4 regressions, live DB/Docker, official research, capability gaps | Complete |
| M1 | Explicit bounded MCP Client, discovery/schema checks, allowlisted reads, actual official-server read | Local implementation passed; live check unverified: credential_missing |
| M2 | Canonical repository/Issue/commit/Snapshot binding, bounded source import, migrations and integrity checks | Pending |
| M3 | Approved controlled GitHub fixture → existing V4 repair → persisted diff/results/test evidence | Pending controlled fixture |
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

## Blockers and resumption

- Required: a credential usable by RepoPilot itself with the official GitHub MCP
  Server. The app's connected GitHub tools do not expose reusable credentials and
  cannot establish that RepoPilot's MCP Client works. Do not extract app secrets.
- Required before controlled integration: owner-selected private test repository
  under juice-gift and three Issues using the preparation plan. No name has been confirmed; do not
  assume the RepoPilot source repository is an authorized repair target.
- Required before actual writes: exact publication proposal and human approval.
  The version authorization alone is not permission to create remote fixtures,
  issues, branches, commits or PRs.
- Docker/DB startup and full live regression are now resolved as recorded above.

Do not ask for raw tokens in chat. Credentials should be configured locally in
ignored environment configuration with minimal repository scope. Implemented M1
setting: `GITHUB_MCP_TOKEN`; begin with read-only Contents/Issues/Pull requests
access to the controlled repository. Empty GITHUB_MCP_ALLOWED_REPOSITORIES denies
repository reads while permitting discovery/identity. Do not use the suggested
repository name as actual authority before Owner creates/confirms and configures it.
Until the credential is available, stop live validation per AGENTS.md §32. V5 is
incomplete; do not issue a Completion Report that implies acceptance. M2–M6,
commit/Snapshot binding and repository/Issue/PR live tests remain outstanding.
