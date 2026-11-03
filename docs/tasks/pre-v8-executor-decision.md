# Container repair execution boundary — decision proposal

Status: owner approved on 2026-11-03 with six mandatory constraints. Implementation in progress; no acceptance claim yet.
The goal requires distinguishing application containers from Agent Sandbox and
escalating major security trust-boundary changes. Current application images do
not contain Docker CLI or mount its socket. Repair therefore fails closed there.

Recommended next implementation, if authorized: a single-purpose local Sandbox
broker, separate from FastAPI/Web and the database, holding local Docker execution
authority. Its only operation runs a registered immutable Python test profile in
the existing restricted executor. It cannot choose a shell, install dependencies,
accept container arguments, read arbitrary host paths, publish to GitHub, or run
application orchestration/model calls.

The request identifies an approved profile, commit, owned workspace/revision and
bounded source/patch bytes. Broker independently loads its own approved registry,
verifies source manifest, editable-path set and revision history before materializing
a private temporary workspace. Tests, image and import root come from broker-owned
policy. Source inputs and responses have hard byte/count limits; requests have a
deadline and bounded single-job admission. Existing Sandbox user/network/caps/
readonly/resource/credential/cleanup checks remain mandatory. Results bind exact
source hashes, profile fingerprint, revision and test evidence. App credentials
never enter this service or child test containers.

Transport should prefer a private local Unix socket on Linux with narrow filesystem
permissions and per-deployment authentication. Windows Docker Desktop requires an
explicitly verified local connection mechanism; never silently bind the broker or
Docker daemon to all network interfaces. A broker container, if used, would be
the only container permitted to access the daemon socket and would be treated as
host-privileged infrastructure even if its Unix user is nonroot. No public listener,
job queue, model framework, multi-agent system or production authentication platform.

Acceptance before calling Compose repair complete: real Issue repair through Web
and container API -> broker -> isolated test containers; same exact revision and
independent tests in final result/proposal; invalid credentials/profile/source/path,
oversized/duplicate/deadline requests and unavailable broker safely fail; restart
and owned-resource cleanup verified; app container never receives daemon access.

Decision needed only after remaining independently authorized audit/documentation
work is complete: authorize this concrete local execution trust boundary, or
explicitly accept host-local API execution as the supported deployment boundary.
The latter is an owner scope/acceptance decision, not a claim that container repair
was already implemented. Remote writes and public hosting remain unauthorized.

## Approved implementation refinement

Owner approval requires fixed server-owned Profiles only, private authenticated
communication, strict path/link/mount validation, unchanged test isolation and
cleanup, minimum broker privilege, and explicit unauthorized/profile/path/timeout/
concurrency tests. Stop if these cannot be met or more host privilege is needed.

Implement Broker as a Linux container with no network, nonroot UID and only the
socket's group access, capabilities dropped, readonly root, and its own private
execution-data volume. API communicates via a separate private Unix-socket volume
and a per-deployment secret file; neither API nor Web mounts the Docker socket.
No host TCP listener is needed on Windows Docker Desktop because both services
use Linux Unix sockets inside the VM. Test bind paths derive ONLY from broker-owned
workspace paths and verified Docker-managed local-volume metadata, never a request.
API sends bounded baseline plus revision deltas; Broker validates approved baseline,
edit allowlist and all revisions, materializes private copies, and runs the existing
fixed executor. Persistent bounded request identities prevent duplicate execution
and preserve ambiguous crash markers. Single-job admission rejects concurrent work.
