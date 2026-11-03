# Trusted-local deployment

This is a single-owner local system without multi-user authentication. Keep it on
a trusted computer. Never expose these services through a public interface,
reverse tunnel, shared proxy or untrusted browser origin. Public hosting is not
authorized. Docker isolation is not a guarantee against hostile code.

## Configuration and startup

Keep the existing host development commands in README. Optional full-stack
containers use the additional `compose.app.yaml`; database-only Compose remains
unchanged. Copy `.env.example` to ignored `.env` and set your database password
and both database URLs. `DATABASE_URL` addresses the host; `CONTAINER_DATABASE_URL`
addresses `database:5432`. URL-encode password characters in URLs. Do not print
expanded `docker compose config` or inspect container environments into reports.

```powershell
docker compose -f compose.yaml -f compose.app.yaml --profile app up --build -d --wait
```

Open http://localhost:8080. Database binds loopback only; API has no published
port. Migration must exit successfully before API starts; Web waits for database
readiness through API. Application containers run nonroot with read-only roots,
capabilities dropped and bounded temporary storage. Build context excludes `.env`,
Git history, virtualenvs and node_modules. Dependencies use uv.lock/package-lock,
base images use immutable digests. The migration service uses the API image.

Container settings explicitly select deterministic providers for reproducible
offline smoke checks. This is not live model evidence. No provider/GitHub secret
is forwarded from the host. To use a real provider, review a private Compose
override explicitly mapping that provider's key/model/base URL. Deployment mode
rejects implicit core defaults and external providers without explicit models
and credentials. Never commit that override or add secrets as build arguments.

`/repositories` mounts only controlled evaluation source read-only. A reviewed
override may replace it with an explicitly trusted input directory. Do not mount
your home directory, `.env`, SSH keys or Docker socket. API images contain no
Docker CLI and do not receive daemon access. The basic stack has no executor and
fails repair closed. The separately owner-approved optional Broker below provides
container repair; host-local API execution remains available for development.

```powershell
docker compose -f compose.yaml -f compose.app.yaml --profile app ps
docker compose -f compose.yaml -f compose.app.yaml --profile app logs --tail 100 api migrate
docker compose -f compose.yaml -f compose.app.yaml --profile app stop web api
docker compose -f compose.yaml -f compose.app.yaml --profile app up -d --wait
```

Never use `down -v` against an existing database. Data persists in the existing
named volume. A restart does not re-run unfinished model calls or publication
writes. Inspect persisted run/proposal state; ambiguous remote outcomes require
the existing read-only reconciliation before another write. No retry middleware
replays POST requests. Keep one API process while host-local execution is used.

## Optional constrained local Sandbox Broker

This boundary was explicitly approved on 2026-11-03; treat Broker daemon access as
host-level authority. Only Broker receives the Docker socket and pinned CLI.
It has no network, runs UID 65534 / socket group 0, drops capabilities and uses a
readonly root. API/Web receive no daemon access. Broker accepts only exact approved
profile/source/revision data; tests/images/mounts/commands are server-owned.

This Broker runtime is verified on Windows Docker Desktop's Linux engine with a
group-0 Docker socket. A differently owned socket requires a separately reviewed
service configuration; no root/privileged fallback is provided.

Build the reviewed immutable Sandbox image and policy first. For a rebuilt image,
generate a NEW runtime policy outside the immutable historical corpus with
`python docs/tasks/pre-v8-build-policy.py --output C:\private\python-profiles.json`
after reviewing the existing `repopilot-tests:pre-v8` image. Pass that file with
the helper's `--policy` and the inspected immutable ID with `--sandbox-image`.
API and Broker mount ONLY that reviewed file readonly at `/policy/profiles.json`
and independently verify its exact SHA256. No request may upload/choose a policy.
The example helper
creates NEW isolated acceptance credentials outside Git; review its fixed project,
ports, image ID and policy digest for another deployment. Retain its private files
for volume restarts; it never prints credentials or overwrites an existing directory.

```powershell
.\apps\api\.venv\Scripts\python.exe docs/tasks/pre-v8-broker-compose-env.py C:\private\repopilot-acceptance
docker build -f apps/api/Dockerfile -t repopilot-api:local .
docker build -f apps/api/Dockerfile.broker -t repopilot-broker:local .
docker compose --env-file C:\private\repopilot-acceptance\compose.env -f compose.yaml -f compose.app.yaml -f compose.broker.yaml --profile app up -d --build --wait
```

Broker authenticates API requests using a per-deployment secret and a 0600 Unix
socket in a private IPC volume. A distinct private API/Web volume carries the API
Unix socket; this optional stack has no API TCP listener. Web remains loopback-only
and exact configured Origin is required for owner operations. API mounts Broker
IPC readonly and cannot read its execution-data volume. Only reviewed source/test
directories are mounted readonly into test containers, never either IPC volume,
daemon socket, credentials or application environment.

Broker verifies actual container/volume metadata before mapping its private owned
directories to daemon paths. Traversal, links, unapproved profiles/options and
changed baseline identities fail closed. Requests are bounded to 8 MB, four
connections with a five-second input deadline and one active test. Sandbox time
and cleanup limits remain fixed. The persistent ledger holds at most 512 request
identities. Full ledgers require operator maintenance while stopped; never delete
ambiguous pending entries to force a retry. Restart takes an exclusive volume lock,
verifies and removes only this deployment's restricted orphan test containers, and
cleans its own abandoned workspaces. Unexpected resources stop startup for review.
Do not scale Broker or share its data volume with another service.

For live models/MCP reads, a private API-only override may map approved provider
credentials and exact models. Never forward these variables to Broker. Remote
publication remains separately unauthorized, even when local repair succeeds.
Final actual evidence is recorded in `docs/evaluation/pre-v8-broker-final-*.json`,
the fresh-policy/Compose reports and the completed HTTP/review flow. The criterion
audit and retained live-model failures are in the completion report.

## Diagnostics

API emits JSON operation metadata: correlation ID, route template, status and
duration; retrieval, generation/tool-calling and Sandbox steps emit bounded
outcomes/timing. Full evidence remains in existing agent traces/evaluation data.
Logs omit request bodies, query strings, source, tool arguments and raw exceptions.
The `X-Request-ID` response header correlates requests; invalid IDs are replaced.
Uncaught server errors return a generic 500. HTTP SDK logging should not be
enabled in environments containing credentials.

## Backup and recovery

Stop API/Web before backup for an application-consistent checkpoint. Use pg_dump
custom format, transfer its binary output with `docker cp` (PowerShell text
redirection can corrupt binary archives), then remove only that temporary file.

```powershell
docker compose exec -T database sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/repopilot-backup.dump'
docker cp repopilot-database-1:/tmp/repopilot-backup.dump ./repopilot-backup.dump
docker compose exec -T database rm /tmp/repopilot-backup.dump
```

Treat backups as sensitive source/Issue/approval data. Store them outside Git.
Restore into a NEW empty database first; never overwrite the original without
explicit approval. Copy archive into the database container, create a separately
named recovery database, and `pg_restore --exit-on-error --no-owner` into it.
Point a private local override at the recovered DB, run Alembic current/check,
and smoke-test before switching. Preserve the original volume until approved.
Publication credentials and external providers must stay disabled during recovery.

## Validation status

GitHub Actions is defined with pinned actions, contents-read permissions and no
model/GitHub secrets. A local successful equivalent is not a GitHub-hosted CI run.
Actual commands/results and remaining acceptance are tracked in
[completed execution plan](tasks/pre-v8-plan.md) and
[completion report](evaluation/pre-v8-engineering-completion.md). The original
development DB still uses its public template credential; new acceptance deployments
use generated private credentials. No existing DB credentials were changed. Keep
the trusted-local boundary; hosted CI remains unexecuted and V8 is unauthorized.

Implementation references: [uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/),
[Compose dependency readiness](https://docs.docker.com/compose/how-tos/startup-order/),
[GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use).
