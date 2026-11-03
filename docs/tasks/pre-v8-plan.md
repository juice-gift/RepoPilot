# Pre-V8 engineering execution plan

Authorization: [owner goal](../goals/pre-v8-engineering.md), 2026-11-03.
Baseline 40ccf6f, clean codex/v6-evaluation, now codex/pre-v8-engineering.
Read-only fetch: origin/main 5316cf8 (V6 merge), tracked V6 branch 5dac7e9.
Preserve local JSX fix. No remote writes, public deployment or V8 authorized.

| Milestone | State | Acceptance |
| --- | --- | --- |
| M0 Preflight | In progress | Existing V4/V5/V6 boundaries, baseline DB/Docker/tests, history |
| A1 Packaging/config | Current | Locked API/Web images, loopback Compose, migration gate, explicit deployment settings, no daemon socket |
| A2 Diagnostics/reliability | Pending | Correlation-safe JSON logs, measured operations, bounded failures, cleanup/restart |
| A3 CI/deployment | Pending | Minimal-permission workflow, real local equivalent checks, smoke/restart/backup/restore |
| B1 Trusted profiles | Pending | Commit-pinned approved Python source/test configurations, reuse workspace/sandbox, fail closed |
| B2 Real repositories | Pending | Two independent real Python repositories; success/failure/refusal/escape scenarios |
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
