# RepoPilot V1 Execution Plan

## Goal

Deliver a debuggable, testable, evidence-grounded repository-level Codebase RAG product from local repository ingestion through inspectable React citations and measured retrieval quality.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| M0 — Foundation Check | Verify the Stage 0 application, database, migration, tests, and Git baseline; make only required reproducibility fixes | Complete |
| M1 — Repository Ingestion | Secure local repository registration, snapshots, scanning, filtering, and inspectable ingestion API | Complete |
| M2 — Code-aware Chunking | Structure-aware Python/TypeScript/JavaScript/TSX/JSX/Markdown chunks with bounded size and citation metadata | Complete |
| M3 — Embedding + Vector Index | Configured embeddings, migration-controlled pgvector storage, idempotent snapshot indexing, and exact vector search | Complete |
| M4 — Retrieval Engine | Independently callable, snapshot-scoped ranked evidence retrieval with explicit API contracts | Complete |
| M5 — RAG Generation + Citation | Bounded context builder, grounded generation, evidence-ID citations, and deterministic citation resolution | In progress |
| M6 — React Product UI | Local repository indexing and question workflow with answer, evidence, citations, and failure/loading states | Not started |
| M7 — Retrieval Quality Improvement / Evaluation | Golden repository, evaluation dataset, vector baseline metrics, evidence-based improvement decision, and recorded results | Not started |

## Current Milestone

M5 — RAG Generation + Citation.

## Milestone Tasks

### M0 — Foundation Check

- Verify the required project documents, Stage 0 implementation, working tree, and Git history.
- Run ordinary backend tests, frontend build, Compose configuration, live migration, and pgvector integration checks.
- Correct only confirmed foundation reproducibility gaps.

### M1 — Repository Ingestion

- Define explicit repository/snapshot/API contracts for a local-path workflow.
- Implement path validation, language detection, recursive scanning, default exclusions, binary/size/minified/generated/sensitive filtering, and content hashing.
- Persist repository and snapshot ingestion records through an Alembic migration and expose thin APIs.
- Test filtering, traversal boundaries, snapshot behavior, API contracts, and live persistence.

### M2 — Code-aware Chunking

- Implement the simplest reliable semantic parsers: Python AST boundaries, brace-aware JS/TS family boundaries, and Markdown headings.
- Split oversized units while preserving line ranges; retain raw content separately from embedding content.
- Persist versioned chunks and expose chunk counts/metadata for debugging.
- Test semantic boundaries, large units, metadata, determinism, and scan-to-chunk integration.

### M3 — Embedding + Vector Index

- Select and document a current supported embedding model and dimensions from official provider documentation.
- Add typed provider configuration and an injectable embedding interface with deterministic test doubles.
- Add migration-controlled vector storage and exact pgvector querying without ANN indexes.
- Implement idempotent snapshot indexing and validate chunk-to-vector persistence with PostgreSQL.

### M4 — Retrieval Engine

- Implement query embedding and exact cosine-distance retrieval scoped to repository and snapshot.
- Return ranked evidence with chunk ID, source metadata, score/distance, and raw content.
- Expose retrieval independently from generation and test cross-snapshot/repository isolation.

### M5 — RAG Generation + Citation

- Implement ordered deduplication, evidence IDs, and bounded explicit context construction.
- Integrate a current supported LLM through an injectable provider boundary.
- Treat repository content as untrusted data and require uncertainty when evidence is insufficient.
- Resolve model-referenced evidence IDs to backend-derived source citations and test mapping independently.

### M6 — React Product UI

- Add typed clients and state for repository ingestion/indexing, retrieval, and grounded questions.
- Present answer and inspectable evidence with file, symbol, line range, score/distance, and chunk content.
- Connect citations to evidence and handle empty, loading, configuration, and failure states.

### M7 — Retrieval Quality Improvement / Evaluation

- Add a controlled Golden Repository and meaningful query-to-expected-evidence dataset.
- Implement and test Hit@K, Recall@K, and MRR calculation.
- Run and record the vector-only baseline, inspect failures, and retain an improvement only if measured results justify it.
- Run final migrations, backend/integration tests, frontend build, end-to-end pipeline validation, scope review, and Git-history review.

## Completed Work

- Required operating, project, V1 goal, and historical Stage 0 documents read in full.
- Stage 0 code, tests, migrations, repository structure, and Git history inspected.
- Working tree confirmed clean on `main` at `1bca31f` before V1 changes.
- Ordinary backend suite and frontend production build passed.
- Docker engine started, PostgreSQL container started, migration head confirmed, and live pgvector integration test passed.
- Ruff declared as a reproducible backend development dependency and six pre-existing import-order findings corrected.
- Added a configured local-filesystem boundary, deterministic supported-language scanner, safety filters, and content-addressed snapshot identity.
- Added migration-controlled repositories, snapshots, and accepted source-file persistence with idempotent repeated ingestion.
- Added repository ingestion/listing APIs, scan evidence, tests, and current setup/API documentation.
- Added independently testable semantic chunking using Python AST functions/classes/methods, Markdown headings, and brace-aware JS/TS family functions/classes.
- Added deterministic size-bounded fallback splitting, versioned chunk metadata, and distinct raw/embedding content.
- Added migration-controlled code-chunk persistence and idempotent chunk creation/listing APIs.
- Added an official OpenAI `text-embedding-3-small` adapter with explicit 512-dimensional output and typed secret-backed configuration.
- Added deterministic normalized token-hash embeddings for reproducible local tests/evaluation, including identifier-aware tokens.
- Added migration-controlled pgvector columns, idempotent snapshot indexing metadata/API, secret redaction for embedding text, and exact cosine search storage primitives.
- Added an independent retriever that validates index/provider identity, embeds questions, and returns ranked evidence with real chunk/source metadata plus cosine score and distance.
- Added the typed `/api/retrieve` contract and live PostgreSQL isolation coverage proving one repository/snapshot cannot return another's chunks.

## Validation Results

- `uv run pytest`: 9 passed, 1 database test skipped.
- `npm run build`: passed TypeScript and Vite production build.
- `docker compose config`: passed.
- `uv run alembic upgrade head` / `uv run alembic current`: passed at `0001_enable_pgvector`.
- `RUN_DATABASE_TESTS=1 uv run pytest`: 10 passed.
- `uv run ruff check src tests migrations`: passed.
- M1 `uv run pytest`: 19 passed, 2 live database tests skipped.
- M1 `RUN_DATABASE_TESTS=1 uv run pytest`: 21 passed.
- `uv run alembic check`: no new upgrade operations detected at `0002_add_repository_ingestion`.
- M1 `npm run build`: passed.
- M2 `uv run pytest`: 25 passed, 3 live database tests skipped.
- M2 `RUN_DATABASE_TESTS=1 uv run pytest`: 28 passed.
- M2 `uv run ruff check src tests migrations`: passed.
- M2 `uv run alembic check`: no new upgrade operations detected at `0003_add_code_chunks`.
- M3 `uv run pytest`: 33 passed, 4 live database tests skipped.
- M3 `RUN_DATABASE_TESTS=1 uv run pytest`: 37 passed, including real pgvector storage and exact cosine search.
- M3 `uv run ruff check src tests migrations`: passed.
- M3 migration upgraded to `0004_add_vector_index`; `uv run alembic check` reported no missing operations.
- Live OpenAI embedding call: not run because no `OPENAI_API_KEY` is configured; adapter request/response contract is covered with a deterministic client fake.
- M4 `uv run pytest`: 36 passed, 5 live database tests skipped (before the final whitespace-contract regression case).
- M4 `RUN_DATABASE_TESTS=1 uv run pytest`: 41 passed, including cross-repository/snapshot retrieval isolation.
- M4 focused retriever/API regression suite: 4 passed; Ruff passed.

## Important Decisions

- Preserve the Stage 0 synchronous FastAPI + SQLAlchemy architecture and database-only Compose boundary.
- Keep each V1 pipeline component explicit and injectable; do not introduce LangChain, LlamaIndex, agent loops, or speculative V2 structures.
- Use exact vector search as the mandatory first retrieval baseline; evaluate before retaining lexical or hybrid improvements.
- Define a snapshot as the deterministic state of accepted, indexable source content; changes to excluded content do not create an index snapshot.
- Store accepted source content so later chunking/indexing is reproducible even if the working repository changes.
- Use standard-library structure parsing for the V1 baseline; syntax failures fall back to bounded file chunks instead of blocking ingestion.
- Keep chunking idempotent for a snapshot and chunking version so stable chunks retain their database evidence IDs.
- Select `text-embedding-3-small` at 512 dimensions based on current official OpenAI model/API documentation; exact pgvector columns deliberately lock this V1 choice.
- Keep deterministic embeddings explicit and labeled as a local evaluation/test provider, not as evidence of external-model quality.
- Keep retrieval entirely independent of generation so ranked source evidence can be inspected and evaluated on its own.

## Blockers

- None.

## Remaining Work

- Execute M5–M7 in order; perform live OpenAI provider checks if credentials become available before final validation.
