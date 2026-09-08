# RepoPilot Stage 0 Execution Plan

## Goal

Complete the engineering foundation for a reproducible local path:

`React -> HTTP -> FastAPI -> PostgreSQL + pgvector`

Stage 0 establishes infrastructure, configuration, database connectivity, migrations, and tests only. It does not introduce any V1 codebase-RAG functionality.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| Task 1 | React, typed health client, FastAPI health API, baseline tests and documentation | Complete (`acedc03`) |
| M1 | Docker Compose PostgreSQL/pgvector infrastructure and safe environment template | Current |
| M2 | Typed settings, SQLAlchemy engine/session foundation, database health API, and tests | Pending |
| M3 | Alembic foundation and migration enabling the `vector` extension without application tables | Pending |
| M4 | Frontend database status, final documentation, clean-database validation, and Stage 0 audit | Pending |

## Current Milestone

M1 — local PostgreSQL/pgvector infrastructure and environment configuration.

## Completed Work

- Stage 0 Task 1 application foundation is committed.
- Existing backend and frontend implementation was reviewed; no Task 1 defect requires rework.
- Current repository structure and Git history were inspected.

## Validation Results

- `uv sync --locked`: passed with Python 3.13.13.
- `uv run pytest`: 1 passed; two upstream TestClient deprecation warnings remain.
- `npm ci`: passed with 0 reported vulnerabilities.
- `npm run build`: passed.
- Docker/PostgreSQL runtime validation: blocked because Docker, Podman, WSL, and `psql` are not installed on this host.

## Important Decisions

- Use the official `pgvector/pgvector:0.8.6-pg17` image for local database infrastructure.
- Containerize PostgreSQL only; React and FastAPI continue to run directly on the host.
- Use one root `.env` file (created locally from `.env.example`) for Compose and backend database settings.
- Use SQLAlchemy 2.x with Psycopg 3 and a synchronous engine/session foundation; synchronous FastAPI routes run database checks in FastAPI's worker thread.
- Let Alembic own `CREATE EXTENSION vector`; do not use container initialization scripts for schema state.
- Do not create vector columns, embedding tables, indexes, or choose embedding dimensions in Stage 0.

## Blockers

- The current machine has no available container runtime or PostgreSQL client/server. Runtime database, pgvector, and clean-database migration validation require Docker Desktop (or an equivalent compatible runtime) to be installed and started.

## Remaining Work

1. Add and statically validate Compose and environment configuration.
2. Add backend settings and database access modules with isolated tests.
3. Add database-backed API health behavior and integration coverage.
4. Add Alembic configuration and the pgvector extension migration.
5. Update the frontend to surface database connectivity.
6. Update README commands and configuration documentation.
7. Run full Stage 0 validation against a clean PostgreSQL database when a compatible runtime is available.
8. Review scope, Git history, and mark Stage 0 complete only after every runtime check passes.
