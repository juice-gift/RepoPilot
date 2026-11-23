# Pre-V8 final security and scope review — 2026-11-03

Scope: trusted single-owner local deployment, the two audited Python projections
and the explicitly approved constrained Broker. This records tested properties
and residual risks; it does not certify public or hostile multi-tenant execution.

| Boundary | Final evidence | Residual limit |
| --- | --- | --- |
| Credentials | 441 repository files scanned before closing docs; provider/Broker/new-deployment credential hits 0, runtime log hits 0, image-config hits 0; final-security-scan.json | Original development DB uses the public template credential found in three existing baseline template/test files. New deployments use generated private credentials; existing DB credentials were not altered |
| Issue/model authority | Strict schemas and fixed profile/baseline/hash/revision; commands, images, host paths, mounts, Docker options and policy uploads denied | Models can produce incorrect code/prose inside the approved edit set; current real Qwen attempts failed safely and earlier unsupported prose remains |
| Paths/source isolation | Workspace/hash/atomic-patch tests, exact baseline, actual Linux inside/outside symlink denial, independent current-source identities and before/after Snapshot checks | Trusted filesystem/admin remains part of the trust base; no hostile shared-host race-proof guarantee |
| Broker transport | Private 0600 Unix socket in 0700 directory, per-deployment credential, duplicate framing/auth/chunked/Expect/malformed/oversize rejection, five-second absolute input deadline, four bounded connections | No public listener; policy/credential files and IPC volume must remain operator controlled |
| Daemon authority | Only Broker receives fixed Docker socket and pinned CLI; nonroot UID, network none, dropped caps, readonly root; private local-volume ownership/mountpoint/resource validation | Broker compromise still confers local Docker authority. Runtime verified only for Docker Desktop Linux/socket group 0; no root fallback |
| Test containers | Actual fixed nonroot/network-none/readonly/caps/seccomp/resources/timeout/credential checks, approved image and independent validation | Tests cover audited projections and bounded assertions; no general hostile-code attestation or arbitrary dependency support |
| Concurrency/retry/crash | One active job; real 429 rejection; process lock; persistent pre-effect identity; exact replay/conflict; force-kill cleanup of fully verified owned orphan and pending retry denial | Unexpected orphan metadata, ambiguous pending state or full ledger requires operator review; no automatic blind retry |
| API/Web owner boundary | Separate private Unix socket volume in Broker mode; no API TCP listener/CLI/socket/execution-data mount; exact Origin and actual Unix address/loopback checked; spoofed forwarding headers denied | Local owner controls are not multi-user/public authentication. Basic mode has no repair executor |
| GitHub approval/publication | Actual MCP reads, exact result/proposal hashes, tree/mode preservation and fake-remote lock/recovery/tamper tests; proposals await approval | No new actual remote write authorized/executed; historical public upstreams fail the unchanged private-owner/current-main gate |
| Dependencies/build | uv/npm locks, pinned application/CLI images, protected test image, no runtime installers/plugins/network installs; npm audit zero findings | Dependency-vulnerability absence outside the checked database/date/runtime is not established |
| CI/network | Pinned action SHAs, contents-read permission, no model/publication secrets, local equivalent checks; loopback host ports, Broker/tests network none | Hosted CI unexecuted; no public deployment/tunnel authorized |
| Scope | Existing V1–V6 components reused; one owner-approved single-purpose Broker, no new Python package/schema or speculative platform | No V8, multi-agent, queue, Redis, Kubernetes, public demo or unrelated refactor |

Actual negative evidence is retained: failing baselines, provider/max-step failures,
unknown semantic output, unsupported explanation, stale test identity, illegal path/
profile/image/approval, unavailable Broker, real timeout and crash ambiguity. Current
container Qwen failures were not tuned away or relabeled as deterministic success.

Final runtime evidence: [Broker checks](pre-v8-broker-final-probe.json),
[transport/links/unavailable service](pre-v8-broker-final-transport-probe.json),
[crash recovery](pre-v8-broker-final-restart-probe.json),
[deployment/persistence](pre-v8-final-deployment-check.json),
[credential scan](pre-v8-final-security-scan.json).
[Completion report](pre-v8-engineering-completion.md) maps every Phase criterion.

The clean test stack is stopped; volumes and original data retained. The accepted
local review stack remains available. No owned Sandbox container remains. Full
implementation whitespace checks pass; the verbatim owner Goal retains intentional
Markdown line-break spaces. Existing Starlette/AnyIO deprecation remains non-blocking.
No further architecture, feature work or tuning is authorized by this closure.