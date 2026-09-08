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
| M4 | Frontend database status, final documentation, clean-database validation, and Stage 0 audit | Complete |

## Current Milestone

Stage 0 is complete. Starting V1 requires a new explicitly active goal.

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
- Added a typed frontend database health client and separate backend/database UI states.
- Updated the root environment template and README for the complete Stage 0 setup and validation flow.
- Bounded unavailable-database checks with an explicit IPv4 host and three-second driver timeout.
- Started PostgreSQL from a clean Compose state, applied and reversed the migration, and restored it to head.
- Corrected the test configuration so isolated tests use explicit settings while the opt-in integration test uses the root development environment.
- Verified the complete browser-to-database path and completed the final Stage 0 scope audit.

## Validation Results

- Docker 29.7.2 and Compose 5.5.1: configuration valid; database container healthy.
- Clean pre-migration state: PostgreSQL 17.11 ready, `vector` available but not installed, and no Alembic revision applied.
- `uv run alembic upgrade head`: applied `0001_enable_pgvector`; `vector` 0.8.6 installed and only `alembic_version` exists in the public schema.
- `uv run alembic downgrade base` followed by `upgrade head`: passed and restored the database to the single migration head.
- `uv sync --locked`: passed with Python 3.13.13.
- `RUN_DATABASE_TESTS=1 uv run pytest`: 10 passed; one upstream Starlette/AnyIO deprecation warning remains.
- `ruff check apps/api/src apps/api/tests apps/api/migrations`: passed.
- `npm ci`: passed with 0 reported vulnerabilities.
- `npm run build`: passed TypeScript and Vite production builds.
- `yamllint -d relaxed compose.yaml`: passed.
- FastAPI/Uvicorn and Vite startup: passed.
- `GET /api/health` and `GET /api/health/database`: HTTP 200 with the expected contracts and CORS origin.
- Browser validation: the React UI reported both `Backend: Connected` and `Database: Connected`.

## Important Decisions

- Use the official `pgvector/pgvector:0.8.6-pg17` image for local database infrastructure.
- Containerize PostgreSQL only; React and FastAPI continue to run directly on the host.
- Use one root `.env` file (created locally from `.env.example`) for Compose and backend database settings.
- Use SQLAlchemy 2.x with Psycopg 3 and a synchronous engine/session foundation; synchronous FastAPI routes run database checks in FastAPI's worker thread.
- Let Alembic own `CREATE EXTENSION vector`; do not use container initialization scripts for schema state.
- Do not create vector columns, embedding tables, indexes, or choose embedding dimensions in Stage 0.

## Blockers

- None.

## Remaining Work

- None within Stage 0.
- V1 work is intentionally excluded and requires a separately authorized goal.
