# RepoPilot

RepoPilot is a long-term AI codebase intelligence and issue-resolution system.

**Stage 0, V1 — Codebase RAG, V2 — Code Intelligence, and V3 — Read-only Repository Agent are complete.**
**V4 — Issue Resolution Agent is complete under its authorized goal.**
M0–M6 deliver private workspaces, patches, Docker tests, bounded repairs and the
API/UI. Two real Qwen positive repairs pass independent tests; the resumed
owner-selected model passes the frozen ambiguity criterion without modifications.
Final regressions pass. See the
[completion report](docs/evaluation/v4-issue-resolution-status.md) and
`docs/tasks/v4-plan.md` for evidence, earlier failures and limitations.
V5 — MCP + GitHub Integration was explicitly authorized on 2026-10-27.
Local preflight passed; implementation awaits MCP credentials. No V5 product
capability or live integration acceptance is claimed. See the [V5 goal](docs/goals/v5-mcp-github.md) and
[execution plan](docs/tasks/v5-plan.md). Stop at V5/V6.

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

V2 adds a separate deterministic path:

```text
Persisted snapshot file content
-> Python AST / JavaScript and TypeScript Tree-sitter syntax
-> symbols, static imports and reference occurrences
-> conservative binding resolution
-> versioned PostgreSQL structural index
-> typed structural navigation API
```

Definitions and source locations come from the structural index. References carry
`resolved`, `unresolved`, or `ambiguous` status plus a reason. This path uses no
embedding or generation provider and never executes repository code. V1 chunking,
retrieval ranking and the evidence UI retain their existing behavior.

## Planned functionality

Version results are recorded in `docs/tasks/v1-plan.md`, `docs/tasks/v2-plan.md`
and `docs/tasks/v3-plan.md`, with completion reports under `docs/evaluation/`.
GitHub/MCP integration, multiple agents and production engineering remain outside
V4. Code modification and controlled sandbox execution belong to the active V4 goal.

V3 adds a separate read-only investigation flow:

```text
Question / issue + repository_id + snapshot_id
-> bounded explicit agent loop -> Responses provider tool calls
-> typed allowlist -> persisted source / V2 symbols / V1 retrieval
-> bounded observations -> next model turn -> final answer + tool trace + sources
```

The five tools are `list_files`, `read_file`, `search_code`, `search_symbol` and
`retrieve_context`. They cannot access host filesystem paths, execute source,
change snapshots or build indexes. Repository content remains untrusted data.
The UI retains V1 retrieval/ask and adds investigation plus expandable observations.
Use **Prepare symbol navigation** to explicitly build the selected snapshot's V2
index before investigation; **Ingest & index** prepares V1 retrieval. Missing
indexes return safe tool failures that the model can inspect.

Engineering and live multi-turn Qwen validation passed; observed answer-grounding
failures remain in the small baseline. See
[`V3 completion and evaluation`](docs/evaluation/v3-repository-agent-results.md).

## V4 controlled issue resolution

`POST /api/agent/resolve` accepts `repository_id`, `snapshot_id`, `profile` and
`issue`. Profiles currently support only the frozen source in
`apps/api/evaluation/resolution_golden/repository`: `fee-days`,
`dispatch-preconditions`, and `ambiguous-cap`. Arbitrary repositories, commands,
images, dependencies and edit permissions are not accepted by this endpoint.

Build the test image from the repository root and configure its immutable ID
in the API process environment before starting/restarting FastAPI:

```powershell
docker build --tag repopilot-tests:v4 apps/api/sandbox
$env:RESOLUTION_SANDBOX_IMAGE = docker image inspect repopilot-tests:v4 --format '{{.Id}}'
```

In the UI, ingest/index `apps/api/evaluation/resolution_golden/repository`, prepare
symbols, select the resulting snapshot/profile, describe its issue and click
**Resolve issue**. For `fee-days`, ask to charge every overdue day while retaining
integer cents, negative-input guards and the 30-day cap. For
`dispatch-preconditions`, ask to authenticate first and reject authorized negative
attempts for both permanent/transient jobs while preserving the existing cap.
For `ambiguous-cap`, ask whether the documented 60 or implemented 300 seconds is
intended; the expected safe outcome requires an owner decision with no changes.

The server copies only verified saved source into a private temporary workspace,
requires an accepted plan and failing baseline before writes, then permits bounded
patch/test repair attempts. Source and independent tests are mounted read-only
into restricted Linux Docker containers. Returned diff/changed source come from
the actual final revision. Test observations carry their exact revision and
expected test count. Completed execution can still mean incomplete repair or
insufficient evidence. The UI shows original/modified code, public plans, tests,
tool trace, diagnostics and stop reason; read-only investigation remains available.

The temporary workspace is cleaned after the synchronous run. Neither original
source nor the saved Snapshot is modified; V1/V2 indexes remain baseline-only
after patches. No product-agent commit/push occurs. See
[`sandbox setup and limits`](apps/api/sandbox/README.md) for isolation details and
concrete limitations. Passing a small independent test set is bounded evidence,
not a proof of arbitrary program correctness. External model results are evaluated
separately from scripted orchestration.

From `apps/api`, opt into actual sandbox and database regression checks:

```powershell
$env:RUN_DATABASE_TESTS = '1'
$env:RUN_SANDBOX_TESTS = '1'
uv run pytest
```

The small frozen repair baseline has separate scripted and real Qwen modes. With
the same prepared image setting, run from `apps/api`:

```powershell
$env:PYTHONPATH = 'src'
uv run python -m repopilot.evaluation.resolution --mode scripted --output ../../docs/evaluation/local-v4-scripted.json
uv run python -m repopilot.evaluation.resolution --mode qwen --output ../../docs/evaluation/local-v4-qwen.json
```

Use `--case ambiguous-cap` for a targeted ambiguity evaluation. Reports preserve
source/Snapshot integrity, exact tested revisions,
actual tool decisions and review hashes; scripted patches are not model success.

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

The zero-cost local setup uses `EMBEDDING_PROVIDER=deterministic`. It produces normalized token-hash vectors for repeatable tests and evaluation, not production semantic quality. External choices are `qwen` and `openai`; their credentials stay in the ignored local `.env`. The V1 live-validated provider is Alibaba Cloud Model Studio / Qwen, using `qwen3.7-text-embedding` with an explicit 512-dimensional output matching the existing pgvector schema. The adapter observes the model's 20-input request limit without changing the indexing pipeline. OpenAI support retains `text-embedding-3-small` at 512 dimensions. Likely secret assignments are redacted from embedding text while raw citation content remains unchanged.

For grounded generation with the V1 live-validated provider, set `GENERATION_PROVIDER=qwen`. Alibaba Cloud Model Studio / Qwen uses `qwen3.7-flash` through the OpenAI-compatible Responses API in the Beijing region. Both external providers preserve the same grounding instructions, untrusted-repository-data boundary, and backend citation resolution. Deterministic providers support reproducible offline tests and evaluation; OpenAI providers are implemented and contract-tested but were not live-tested for V1.

`RETRIEVAL_STRATEGY=hybrid` is the measured V1 default. It reranks exact-vector results using a small lexical score over the same metadata-enriched chunk content. Set it to `vector` to reproduce the mandatory vector-only baseline. The measured comparison and limitations are recorded in `docs/evaluation/v1-retrieval-results.md`.

Investigation reuses `GENERATION_PROVIDER` and its existing Qwen/OpenAI model
settings. `deterministic` runs a retrieve/read workflow for local verification,
not LLM investigation. Default bounds are 12 model turns including the final
answer, five calls per turn, 4,000 characters per argument object, 12,000 per
serialized observation, 60,000 for accumulated input including instructions and
tool schemas, and 12,000 for model output. Configure the four `AGENT_*` values
in `.env.example`; generation also retains `GENERATION_MAX_OUTPUT_TOKENS`.
Each agent model request has a 30-second timeout and no SDK retry. Character
budgets are application limits, not tokenizer measurements.

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
- `POST /api/agent/investigate` runs read-only multi-turn investigation over one saved repository snapshot and returns the final answer, trace, sources, stop reason and diagnostics.

V2 endpoints share the prefix
`/api/repositories/{repository_id}/snapshots/{snapshot_id}/structure`:

| Method and suffix | Purpose |
| --- | --- |
| `POST /index` | Explicitly build/reuse the current structural index |
| `GET /files` | List persisted files, including before structural indexing |
| `GET /symbols` | List symbols; filter with `file_path`, or search `q` with `match=exact`, `qualified`, or `normalized` |
| `GET /symbols/{symbol_id}` | Return the definition metadata and saved source lines |
| `GET /symbols/{symbol_id}/references` | List only references resolved to this exact symbol |
| `GET /references` | Inspect occurrences; filter by `file_path` and `status` |
| `GET /imports?file_path=...` | Static dependencies including unresolved occurrences |
| `GET /importers?file_path=...` | Reverse lookup of resolved local dependencies |

List endpoints accept `limit` (1–500, default 100) and `offset` (default 0).
Source lines are one-based and inclusive; occurrence columns are one-based UTF-8
byte offsets. Duplicate symbol names return separate definitions. Queries never
guess which duplicate the caller meant. Missing resources return 404; queries
requiring a missing/older structural index return 409; syntax failures and invalid
inputs return 422. A syntax failure aborts the structural rebuild and preserves
the previous index; it does not change V1's chunking fallback behavior.

Python resolves static absolute imports using the repository root and source
roots inferred from package markers, plus relative imports. Ambiguous roots stay
ambiguous. JS/TS resolves relative modules and explicit exported definitions;
package aliases, export-list/re-export chains, dynamic loaders, runtime mutation,
and type-dependent member dispatch remain outside the baseline. Markdown stays
available for V1 RAG and file navigation without structural symbols.

An investigation request contains only `repository_id`, `snapshot_id` and a
nonempty `question` (maximum 4,000 characters). Model tool arguments cannot
override either ID. Missing snapshots return 404; missing model configuration or
an initially unavailable database returns 503. A started run returns HTTP 200
with an inspectable result even when incomplete; always check `stop_reason`.
Possible reasons are `completed`, `max_steps`, `context_limit`,
`model_output_limit`, `invalid_model_response`, `provider_failure`, and
`tool_failure`. `completed` means the model returned a final answer, not that
its claims were independently proven.

`max_steps` counts model turns; `total_steps` counts executed tool calls, which
can share a model turn. Trace entries contain validated arguments (null for
rejected calls), execution status, duration and bounded observation. No reasoning
items or intermediate model prose are recorded. Known input/resource/index
failures can be returned to the model for recovery; unexpected infrastructure
failures stop the run. Source IDs such as `[E2_1]` are minted by the backend;
invalid bracketed IDs are replaced and reported. This validates source identity,
not the truth of every sentence. Symbol-only results carry definition metadata;
behavioral claims require source inspection.

`read_file` uses validated POSIX relative paths and one-based inclusive ranges,
defaulting to 100 lines and limiting each request to 200. `search_code` is a
case-sensitive literal substring baseline over persisted PostgreSQL source;
SQL wildcards are escaped and results are ordered by file and line. Search/list
limits and output truncation can omit items; `omitted_items` is a lower bound,
not a total-count query. No regex engine or new search service is introduced.

The V1 live-validated external provider is Alibaba Cloud Model Studio / Qwen: `qwen3.7-text-embedding` produces 512-dimensional embeddings, and `qwen3.7-flash` performs grounded generation through the OpenAI-compatible Responses API. Requests use `store=false`, an explicit output bound, and grounding instructions separated from untrusted repository content. The deterministic local provider is an extractive pipeline test aid, not an LLM-quality substitute.

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

The complete suite also verifies structural persistence, isolation, concurrent
idempotency, imports, references, API contracts and frozen evaluation. Migration
replay creates and removes its own uniquely named disposable database; this test
requires local database creation permission. It never drops the configured
development database. The current migration head is `0005_structural_index`.

Backend lint, from `apps/api`:

```bash
uv run ruff check src tests migrations
```

Frontend TypeScript validation and production build, from `apps/web`:

```bash
npm run build
```

Run the checked-in retrieval evaluation against the live migrated database from `apps/api`.

PowerShell:

```powershell
$env:PYTHONPATH = "src"
uv run python -m repopilot.evaluation.runner --strategy vector --top-k 5
uv run python -m repopilot.evaluation.runner --strategy hybrid --top-k 5
Remove-Item Env:PYTHONPATH
```

macOS or Linux:

```bash
PYTHONPATH=src uv run python -m repopilot.evaluation.runner --strategy vector --top-k 5
PYTHONPATH=src uv run python -m repopilot.evaluation.runner --strategy hybrid --top-k 5
```

Run the independent frozen V2 structural evaluation from `apps/api`:

```powershell
$env:PYTHONPATH = "src"
uv run python -m repopilot.evaluation.structural
Remove-Item Env:PYTHONPATH
```

On macOS/Linux use `PYTHONPATH=src uv run python -m repopilot.evaluation.structural`.
Use `--output path.json` to save the report. The checked-in structural dataset and
normalized source hashes are frozen. Perfect scores on this small labeled corpus
do not imply complete reference resolution on arbitrary repositories.

Run the frozen V3 multistep orchestration baseline from `apps/api`:

```powershell
$env:PYTHONPATH = "src"
uv run python -m repopilot.evaluation.agent --output ../../docs/evaluation/local-agent-report.json
# Conditional external check, with the existing ignored Qwen credential:
uv run python -m repopilot.evaluation.agent --mode qwen --output ../../docs/evaluation/local-qwen-report.json
Remove-Item Env:PYTHONPATH
```

The four-file corpus and three tasks are checksum-frozen. The scripted mode tests
actual tools, saved data, multi-turn orchestration and evidence discovery; its
prewritten answers do not measure LLM decisions. Qwen mode uses real tool calling
and deterministic retrieval embeddings to keep model investigation separate from
embedding quality. Raw evaluation leaves `grounded_final_answer` unreviewed.
Compare claims against the saved source, then record boolean verdicts/reasons
with matching `review_hash` and apply them using `--review-report` and `--reviews`.
The checked-in initial/trial reports retain incorrect claims rather than changing
ground truth. The completion report explains the remaining two failed trial cases.

The additional parser dependencies are `tree-sitter`, `tree-sitter-javascript`
and `tree-sitter-typescript`. The lockfile uses Tree-sitter 0.25.2: 0.26.0 caused
a native Windows crash on the actual React TSX source, so the supported range
currently stays below 0.26 with subprocess regression coverage. The algorithm
version is `structural-v2`; bump this version when extraction/resolution semantics
change so existing snapshots rebuild from their persisted content.

After configuring `DASHSCOPE_API_KEY` in the ignored root `.env`, the Qwen
live-provider check can be reproduced from `apps/api`. It embeds the 19 Golden
Repository chunks with `qwen3.7-text-embedding`, asks one grounded question
through `qwen3.7-flash`, and succeeds only when the answer contains a valid
backend-resolved evidence citation. It never prints the key. This command was
used for the completed V1 external-provider validation.

PowerShell:

```powershell
$env:PYTHONPATH = "src"
uv run python -m repopilot.evaluation.live_provider --provider qwen
Remove-Item Env:PYTHONPATH
```

macOS or Linux:

```bash
PYTHONPATH=src uv run python -m repopilot.evaluation.live_provider --provider qwen
```

Stop local infrastructure from the repository root:

```bash
docker compose down
```
