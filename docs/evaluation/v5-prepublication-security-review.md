# V5 prepublication security and scope review

2026-10-28. This is an implementation review before human publication approval,
not the V5 Completion Report. M0–M4 are complete; M5 live writes and M6 final
acceptance remain pending. No repair branch, commit or PR has been published.

Reviewed code commits: M4 `ed8cc3a`, M5 implementation `4f0f5b6`. Checks ran on
the reviewed M5 working tree before its commit; the V4 runner records the HEAD at
invocation (`ed8cc3a`), not an assertion that all then-uncommitted V5 files were
already committed. The frozen source and protected test manifest are unchanged.

## Implemented boundaries reviewed

| Boundary | Evidence / result |
| --- | --- |
| Real MCP | Official endpoint, SDK 2.3.0, negotiated 2026-07-28; discovery plus actual repository/Issue/commit/source/PR-list reads. Publication tool schemas and exact arguments validate against real discovery. |
| Untrusted input | Server descriptions, remote source/Issues/PRs and model prose cannot change policy. Fixed tools, endpoints, bounded responses, schema validation; ordinary/dynamic/recursive remote schema references rejected. Remote links are not downloaded. |
| Execution | Only exact frozen five-file source and three original Issue contracts. Existing private workspaces, approved immutable Docker image, no network/credential forwarding, protected local tests and cleanup remain intact. |
| Provenance | Numeric GitHub repo identity, immutable commit, saved Snapshot and Issue body digest. Saved result, test revision, complete patch-history hash chain and final diff are rebuilt before proposal approval and publication. |
| Approval | Server generates full immutable plan; SHA256 binds destination, baseline, branch, files, diff, test result, deterministic commit and PR metadata. Local-owner Origin/loopback controls, explicit confirmation text, empty-by-default write allowlist; no model approval tool. |
| Writes | Narrow Git API permits only exact approved tree, commit and create-only branch payloads. No PATCH, update-ref, force, delete, default-branch write or merge. Official MCP write session permits only exact draft-PR arguments. |
| Baseline | Checks before every missing write and after publication. Exact parent/tree/modes/content verified. Main movement invalidates approval, preserving partial effects. PR creation cannot atomically CAS its base; this concrete limit is disclosed in the approval plan. |
| Recovery | Persist publishing marker before effects; hold PostgreSQL row lock while publishing. Retry first reads content-addressed objects, dedicated ref and filtered PR marker. Ambiguous outcomes retain safe errors; collisions or changed metadata stop. Published repeats return historical evidence without mutations. |
| Secrets | Ignored .env → SecretStr → fixed official TLS destinations. No command-line Token, prompt, Sandbox, DB result or report. Network/SDK exception text is sanitized and private transport logs suppressed. |

## Validation actually performed

- Latest full DB/Docker/actual-MCP regression: **329 passed, zero skips**. The
  **35 passing focused proposal/publication regressions** include patch-history
  tampering and main movement during remote steps. One existing AnyIO deprecation
  warning remains; no test failure is concealed.
- `uv run ruff check src tests migrations`: passed. Changed Python files formatted.
  An optional whole-tree formatter check reported 21 pre-existing style differences;
  those unrelated files were not reformatted. Initial fixable lint findings were
  corrected before the passing checks.
- `uv run alembic current` / `check`: 0008 head, no drift. Full suite includes clean
  migration upgrade/downgrade/replay in a disposable database, preserving sentinel data.
- `npm run build`: TypeScript and production Vite build pass. No configured frontend
  lint/test script exists. Browser smoke confirms saved real results, exact proposal
  fields and disabled unapproved publication. No approval checkbox was selected.
- V1 vector and hybrid CLI regressions preserve .75/.875/1 hit rates and .8375 MRR@5
  for vector, all 1 for hybrid. V2 structural and V3 scripted checks pass. V4 scripted
  mode with real Docker meets all three frozen conditions. Reports are named
  `v5-prepublication-v1-*`, `v2-structure`, `v3-scripted`, `v4-scripted` in this folder.
  Scripted reports do not claim actual model accuracy or remote integration proof.
- Real MCP prepublication checks for both saved Qwen runs pass. Four fixed Git API
  GETs per plan verify repo identity, unchanged main, exact flat 100644 baseline tree
  and absent target ref. No mutation was used to infer PAT scope.
- Mock transport/fault injection tests cover exact parameters, default-branch/foreign
  ref denial, parent/tree/PR tampering, no approval, scope denial, permissions, stale
  baseline before/during effects, ambiguous success, crash marker, concurrency,
  redirects, bounded output and no blind network retries. They are local tests only.

## Scope audit and remaining acceptance

Changed responsibilities: github proposals/approval, fixed Git object API supplement,
official MCP PR adapter, synchronous publication/reconciliation, thin `/api/github`
routes and React controls. Migration 0008 adds durable proposals. No new dependency
in M4/M5; V5's MCP SDK, httpx2 and jsonschema additions solve the actual protocol,
bounded transport and tool schema responsibilities recorded in M1.

No frozen repository/test/manifest changes, arbitrary execution profiles, multi-agent
system, background worker/queue, general authentication, merge, deployment, V6
evaluation platform or V7 capability. React/FastAPI/PostgreSQL and existing V1–V4
interfaces remain. Local single-owner Origin control is not production security.

Known limits: frozen fixtures only; trusted local machine; first-page bounded reads;
repository role flags do not prove fine-grained PAT write scopes; MCP's curated PR
view omits maintainer-can-modify (false is requested, not claimed independently read
back). Main can change between checks; immutable orphan objects and partial dedicated
branches/PRs can remain. They are never automatically overwritten or deleted.

Acceptance 1–3, 6–7 have passing implementation/read-only/regression evidence.
Acceptance 4–5 still require separately approved **actual** publication and exact
remote verification. Acceptance 8 requires the final Completion Report after that
verification and final regressions. The full version remains incomplete.

Concrete combined approval: [two exact publication plans](../tasks/v5-publication-approval.md),
with [machine-readable plans and live read evidence](v5-publication-proposals.json).
