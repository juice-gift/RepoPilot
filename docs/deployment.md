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
Docker CLI and do not receive daemon access. Sandbox repair consequently fails
closed there. Use the existing host-local API with the immutable sandbox image
for repair workflows. This container stack does not yet provide a remote Sandbox
execution service; adding one requires a separately reviewed security design.

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
[execution plan](tasks/pre-v8-plan.md); the entire pre-V8 goal is still in progress.

Implementation references: [uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/),
[Compose dependency readiness](https://docs.docker.com/compose/how-tos/startup-order/),
[GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use).
