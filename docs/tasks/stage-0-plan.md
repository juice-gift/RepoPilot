# RepoPilot Stage 0 Execution Plan

## Goal

Complete the engineering foundation for a reproducible local path:

`React -> HTTP -> FastAPI -> PostgreSQL + pgvector`

Stage 0 establishes infrastructure, configuration, database connectivity, migrations, and tests only. It does not introduce any V1 codebase-RAG functionality.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| Task 1 | React, typed health client, FastAPI health API, baseline tests and documentation | Complete (`acedc03`) |
| M1 | Docker Compose PostgreSQL/pgvector infrastructure and safe environment template | Complete |
| M2 | Typed settings, SQLAlchemy engine/session foundation, database health API, and tests | Complete |
| M3 | Alembic foundation and migration enabling the `vector` extension without application tables | Complete |
| M4 | Frontend database status, final documentation, clean-database validation, and Stage 0 audit | Current |

## Current Milestone

M4 — frontend database status, documentation, and final Stage 0 validation.

## Completed Work

- Stage 0 Task 1 application foundation is committed.
- Existing backend and frontend implementation was reviewed; no Task 1 defect requires rework.
- Current repository structure and Git history were inspected.
- Added a database-only Compose service using PostgreSQL 17 with pgvector 0.8.6.
- Added a safe root environment template; local `.env` files remain ignored.
- Added required typed settings, SQLAlchemy engine/session lifecycle, and a database-backed health route.
- Added isolated tests for configuration, session setup, connectivity behavior, and API success/failure responses.
- Added Alembic configuration and one migration that enables only the `vector` extension.
- Added opt-in live database coverage for the API, migration revision, and pgvector availability.

## Validation Results

- `uv sync --locked`: passed with Python 3.13.13.
- `uv run pytest`: 1 passed; two upstream TestClient deprecation warnings remain.
- `npm ci`: passed with 0 reported vulnerabilities.
- `npm run build`: passed.
- `yamllint -d relaxed compose.yaml`: passed after resolving its only style warning.
- `uv sync --locked`: passed after adding database dependencies.
- `uv run pytest`: 9 passed; one upstream Starlette/AnyIO deprecation warning remains.
- `ruff check apps/api/src apps/api/tests`: passed.
- `uv run alembic heads` / `history`: one head at `0001_enable_pgvector`.
- `uv run alembic upgrade head --sql`: passed; generated `CREATE EXTENSION IF NOT EXISTS vector` and no application schema.
- `uv run alembic downgrade 0001_enable_pgvector:base --sql`: passed; generated the matching extension downgrade.
- `uv run pytest`: 9 passed and the live database test skipped while no database runtime is available.
- `ruff check apps/api/src apps/api/tests apps/api/migrations`: passed.
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

1. Update the frontend to surface database connectivity.
2. Update README commands and configuration documentation.
3. Run full Stage 0 validation against a clean PostgreSQL database when a compatible runtime is available.
4. Review scope, Git history, and mark Stage 0 complete only after every runtime check passes.
