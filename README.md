# RepoPilot

RepoPilot is a long-term AI codebase intelligence and issue-resolution system.

**Stage 0 — Project Inception is complete. V1 — Codebase RAG has not started yet.**
## Current functionality

Stage 0 provides a local development foundation with this request path:

```text
React UI
-> HTTP health clients
-> FastAPI routes
-> SQLAlchemy session
-> PostgreSQL 17 with pgvector
```

The UI reports backend and database connectivity separately. Alembic owns the database migration state and currently enables only the PostgreSQL `vector` extension. There are no application, embedding, or vector tables yet.

## Planned functionality

Later versions may add repository ingestion, code-aware retrieval, RAG, issue analysis, agent workflows, GitHub/MCP integration, evaluation, and production engineering. These capabilities are planned only and are not part of Stage 0.

## Repository structure

```text
RepoPilot/
├── apps/
│   ├── api/
│   │   ├── migrations/   # Alembic migration history
│   │   ├── src/          # FastAPI, settings, and database access
│   │   └── tests/        # Isolated and opt-in database tests
│   └── web/              # React + TypeScript frontend
├── docs/                 # Project charter and execution plans
├── .env.example          # Safe local configuration template
├── compose.yaml          # Local PostgreSQL/pgvector service
├── AGENTS.md
└── README.md
```

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Node.js 22.12 or later
- npm
- Docker Desktop or another Docker Compose-compatible runtime

React and FastAPI run directly on the host. Docker Compose is used only for the local database.

## Configure the environment

From the repository root, create the ignored local configuration file:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

The example contains local-only placeholder credentials. If you change `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, or `POSTGRES_PORT`, update `DATABASE_URL` to match. Its three-second connection timeout and explicit IPv4 loopback address keep database health failures bounded. The backend fails at startup with a configuration error when `DATABASE_URL` is absent or does not use the `postgresql+psycopg://` scheme.

## Start PostgreSQL

From the repository root:

```bash
docker compose up -d database
docker compose ps
```

The Compose health check reports when PostgreSQL is ready. Database data is stored in the named `postgres_data` volume and is preserved by `docker compose down`.

## Install dependencies

Backend, from `apps/api`:

```bash
uv sync
```

Frontend, from `apps/web`:

```bash
npm ci
```

## Apply migrations

With PostgreSQL running, execute from `apps/api`:

```bash
uv run alembic upgrade head
uv run alembic current
```

The initial migration enables pgvector. Verify it directly when using the unchanged example database names:

```bash
docker compose exec database psql -U repopilot -d repopilot -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```

## Run locally

Start the backend from `apps/api`:

```bash
uv run uvicorn --app-dir src repopilot.main:app --reload
```

The API is available at `http://localhost:8000`:

- `GET /api/health` checks the FastAPI service without querying PostgreSQL.
- `GET /api/health/database` executes `SELECT 1` through SQLAlchemy and returns HTTP 503 when PostgreSQL is unavailable.

Start the frontend in another terminal from `apps/web`:

```bash
npm run dev
```

Open `http://localhost:5173`. Vite reads `VITE_API_BASE_URL` from the root `.env` file; FastAPI reads `DATABASE_URL` and `FRONTEND_ORIGIN` from the same file.

## Run validation

Backend tests that do not require a live database, from `apps/api`:

```bash
uv run pytest
```

Run the complete backend suite after starting PostgreSQL and applying migrations.

PowerShell:

```powershell
$env:RUN_DATABASE_TESTS = "1"
uv run pytest
Remove-Item Env:RUN_DATABASE_TESTS
```

macOS or Linux:

```bash
RUN_DATABASE_TESTS=1 uv run pytest
```

The live test verifies the database health API, Alembic revision, and installed pgvector extension.

Frontend TypeScript validation and production build, from `apps/web`:

```bash
npm run build
```

Stop local infrastructure from the repository root:

```bash
docker compose down
```
