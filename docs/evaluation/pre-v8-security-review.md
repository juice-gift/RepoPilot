# Pre-V8 security review — 2026-11-03

This is a trusted single-owner local system. The evidence below distinguishes
automated guarantees, actual runtime observations and remaining risks. It does
not certify arbitrary hostile-code execution or public hosting.

| Boundary | Evidence and result | Limit |
| --- | --- | --- |
| Secrets | test_github_mcp credential/header/redaction cases; test_diagnostics uses sensitive body/query/header/exception sentinels; configured-secret scans of generated evidence found zero matches | Operator must protect ignored environment files, backups and provider configuration; do not enable raw SDK debug logs |
| Injection and authority | Model/Issue cannot set registry path/hash, image, shell, command or container flags. Invalid paths, edits, tools and schemas are denied before effects. Real ambiguity trial made zero modifications | A model can still write incorrect code or explanations inside approved Python files; source review found a real unsupported timestamp-interval explanation |
| Paths and links | Workspace unsafe-path/collision/symlink/out-of-band-change tests; atomic multifile patch and rollback; registry symlink/junction denial; source and policy hashes | Trusted filesystem/admin remains part of the trust base; not a race-proof hostile multi-user host |
| Source/Snapshot isolation | Actual owned-evaluation before/after source and Snapshot comparisons, exact-revision tests and cleanup; original repositories never imported/executed on host | Inputs are reviewed package-source projections, not unrestricted full repository execution |
| Sandbox | Real Linux Docker preflight: UID/GID 65534, readonly root/inputs, network none, seccomp, no-new-privileges, caps dropped, bounded CPU/memory/pids/output/deadline, no credentials/socket | Docker/host kernel remain trusted. Protected pytest is an engineering test oracle, not adversarial remote attestation against malicious Python manipulating its own interpreter |
| Cleanup | Actual timeout/cancellation/output/resource-limit probes and exact owned-container cleanup; both real corpus runs clean workspaces and exact-path owned DB rows | Abrupt host death/SIGKILL can interrupt finally blocks. Inspect exact owned labels/names after a crash; never blindly remove unrelated containers |
| Daemon access | Application container inspect confirms no Docker socket/CLI; sandbox input mounts contain only source and independent validation | Host-local API/executor has local Docker authority. Container repair is currently unavailable rather than receiving uncontrolled daemon authority |
| Remote credentials | Official endpoint only, no redirects, fixed tool/REST operation schemas, exact repository allowlists, token exclusion/redaction tests; actual MCP reads of both approved public repositories | Existing credential's GitHub-side scopes are managed by the owner; application checks do not enlarge them |
| Approval and publication | Real DB precise hash/tamper/origin tests, immutable plan/result/revision/policy identity; nested tree blob/mode preservation; changed content invalidates authorization | Local owner controls are not multi-user authentication. Proxy clients do not acquire owner identity merely by setting headers |
| Concurrent effects/retries | PostgreSQL row locks, durable publishing marker, exact branch/parent/tree/PR checks; ambiguous tree/commit/branch/PR fake-remote outcomes reconcile with no duplicate effects | New actual remote writes were not authorized or executed; fake outcomes are contract evidence only |
| Dependencies | Locked uv/npm and hash-pinned Sandbox dependencies; no setup hooks/project plugins/network installs in test execution; Vite/source-map-js security fixes; npm audit zero findings at check | General dependency-vulnerability absence is not proven; only the checked advisory/database/runtime scope is claimed |
| CI | Exact action SHAs, contents-read only, no model keys or publication calls, reviewed runtime image policy kept separate from immutable historical fixtures | Workflow not executed on GitHub; local equivalents do not establish hosted CI success |
| Network | Application/database Compose ports bind 127.0.0.1; actual fresh stack healthy; sandbox network none. Host verification services bind 127.0.0.1 | No public authentication/authorization/isolation exists; no public deployment/tunnel is approved |

Actual failure handling includes provider failure at revision zero, model turn
exhaustion despite independently passing code, failed baseline tests, stale test
revision rejection, wrong image/policy rejection, path escape refusal, altered
approval/result denial, unavailable Docker and forced timeout cleanup. These
failures are retained rather than rewritten as successful trials.

No remote push, branch, commit, PR, merge or deletion was performed by this goal.
The two real upstream proposals remain awaiting approval and would additionally
fail the unchanged private-owner/current-main publication guard. A separately
approved private controlled target/policy is required for a publishable repair.

Open deployment acceptance issue: the full Compose application presently provides
ingestion/indexing/navigation/RAG/review, while Sandbox repair runs through the
host-local API. The container stack cannot claim complete Issue Resolution support
until a bounded execution boundary is implemented or the owner explicitly accepts
the documented host-local execution deployment. Do not mark the full goal achieved
by treating this unavailable capability as passing.
