# RepoPilot

RepoPilot is a long-term AI codebase intelligence and issue-resolution system.

**Stage 0 — Project Inception is complete. V1 — Codebase RAG is in progress.**
## Current functionality

The Stage 0 foundation and the V1 application pipeline currently provide:

```text
React UI
-> HTTP health clients
-> FastAPI routes
-> SQLAlchemy session
-> PostgreSQL 17 with pgvector

Local repository path
-> configured filesystem boundary
-> deterministic scan and safety filters
-> content-addressed snapshot
-> PostgreSQL repository, snapshot, and source-file records
-> code-aware chunks
-> configured embeddings and exact pgvector search
-> ranked retrieval evidence
-> bounded grounded generation
-> backend-resolved source citations
-> evidence-first React workflow
```

The UI reports backend and database connectivity separately, ingests and indexes an allowed local repository, and keeps ranked evidence visible alongside retrieval-only diagnostics or a grounded answer. Citation controls focus the exact evidence card used by the answer. Alembic owns the database migration state and enables pgvector plus the V1 ingestion, chunk, and 512-dimensional vector fields.

The ingestion scanner currently supports Python, TypeScript, JavaScript, TSX, JSX, and Markdown. It excludes common dependency/build directories, unsupported and oversized files, binary/non-UTF-8 content, generated/minified files, and sensitive filenames such as `.env`, private keys, credentials, and secrets.

## Planned functionality

The remaining V1 milestone adds a controlled Golden Repository, retrieval metrics, and a measured quality decision. Agent workflows, GitHub/MCP integration, and production engineering belong to later versions.

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

`REPOSITORY_ALLOWED_ROOT` is the only filesystem tree the ingestion API may read. The example value `.` means the RepoPilot project root regardless of the backend process working directory. Set it to a broader absolute development directory only when you intentionally need to ingest repositories there.

The zero-cost local setup uses `EMBEDDING_PROVIDER=deterministic`. It produces normalized token-hash vectors for repeatable tests and evaluation, not production semantic quality. To use the external provider, set `EMBEDDING_PROVIDER=openai` and provide `OPENAI_API_KEY`. V1 selects [`text-embedding-3-small`](https://developers.openai.com/api/docs/models/text-embedding-3-small) with an explicit 512-dimensional output supported by the official [embeddings API](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create). Likely secret assignments are redacted from embedding text while raw citation content remains unchanged.

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
- `POST /api/repositories/ingest` scans an allowed local path and creates or reuses a content-addressed snapshot.
- `GET /api/repositories` lists registered local repositories.
- `GET /api/repositories/{repository_id}/snapshots` lists a repository's immutable snapshots.
- `POST /api/repositories/{repository_id}/snapshots/{snapshot_id}/chunks` creates or reuses the current code-aware chunks.
- `GET /api/repositories/{repository_id}/snapshots/{snapshot_id}/chunks` lists inspectable chunk metadata and content.
- `POST /api/repositories/{repository_id}/snapshots/{snapshot_id}/index` creates or reuses all snapshot embeddings and records model, dimensions, count, and duration.
- `POST /api/retrieve` independently returns ranked, snapshot-scoped evidence with chunk IDs, source locations, cosine score/distance, and raw content; it never invokes answer generation.
- `POST /api/ask` retrieves evidence, builds bounded untrusted-data context, generates a grounded answer, and resolves `[E#]` references into backend-derived citations.

V1 selects [`gpt-5.6-luna`](https://developers.openai.com/api/docs/models/gpt-5.6-luna) for cost-conscious external generation through the official [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create). Requests use `store=false`, an explicit output bound, and grounding instructions separated from untrusted repository content. The deterministic local provider is an extractive pipeline test aid, not an LLM-quality substitute.

Example ingestion request from the repository root configured by `.env.example`:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/repositories/ingest `
  -ContentType application/json `
  -Body '{"path":".","name":"RepoPilot"}'
```

Chunking uses Python AST declarations, Markdown heading sections, and lightweight brace-aware JavaScript/TypeScript family declarations. It prefers functions, Python methods/classes, and headings, falls back safely for invalid syntax, and caps every chunk at 4,000 characters and 160 lines. Raw source remains separate from the metadata-enriched embedding text.

Start the frontend in another terminal from `apps/web`:

```bash
npm run dev
```

Open `http://localhost:5173`. Vite reads `VITE_API_BASE_URL` from the root `.env` file; FastAPI reads `DATABASE_URL` and `FRONTEND_ORIGIN` from the same file. The three-column workspace becomes a single-column flow on narrow screens and exposes explicit loading, empty, configuration, request-failure, answer, citation, and retrieval-evidence states.

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
