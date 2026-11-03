# Container repair execution boundary — decision proposal

Status: reviewable design only; no new service or daemon permission implemented.
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
