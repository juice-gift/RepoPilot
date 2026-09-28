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
| M5 — RAG Generation + Citation | Bounded context builder, grounded generation, evidence-ID citations, and deterministic citation resolution | Complete |
| M6 — React Product UI | Local repository indexing and question workflow with answer, evidence, citations, and failure/loading states | Complete |
| M7 — Retrieval Quality Improvement / Evaluation | Golden repository, evaluation dataset, vector baseline metrics, evidence-based improvement decision, and recorded results | Complete |

## Current Milestone

V1 complete. Final Qwen external-provider validation, regression validation, retrieval evaluation, frontend build, security audit, and scope audit passed. Stop before V2.

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
- Added an explicit ordered/deduplicated context builder with request-scoped evidence IDs, evidence-count limit, and conservative character budget/truncation.
- Added a grounded OpenAI Responses adapter using `gpt-5.6-luna`, `store=false`, no tools, bounded output, and separated untrusted repository input.
- Added deterministic extractive generation for local end-to-end validation, authentic backend citation resolution, invalid-ID removal, and `/api/ask` answer/evidence diagnostics.
- Added typed frontend clients for repository/snapshot/index, independent retrieval, and grounded-answer API contracts with shared structured error handling.
- Replaced the Stage 0 status page with an evidence-first workflow for ingestion/indexing, snapshot selection, retrieval-only inspection, grounded answers, focused citations, and source cards.
- Added explicit connection, empty, loading, configuration, and request-failure states plus responsive three-, two-, and one-column layouts.
- Added an 8-file Golden Repository and frozen 8-question dataset with file-and-symbol relevance judgments.
- Added independently tested Hit@K, Recall@K, and MRR@K calculation plus a CLI runner that exercises ingestion, chunking, embedding, pgvector, and retrieval.
- Measured the exact-vector baseline, identified two ranking failures, and retained a small lexical rerank only after it improved the frozen dataset without regression.
- Exposed `RETRIEVAL_STRATEGY=vector|hybrid`; the evidence-backed hybrid strategy is the V1 default while vector remains reproducible.
- Added a minimal live-provider verifier that embeds the Golden Repository through OpenAI, generates one grounded Responses answer, and requires at least one valid backend-resolved citation before reporting success.
- Added Qwen embedding and Responses generation adapters inside the existing provider boundaries, retaining deterministic and OpenAI providers.
- Configured `qwen3.7-text-embedding` at 512 dimensions and selected `qwen3.7-flash` for grounded generation through the Beijing workspace endpoint.
- Adapted the live-provider verifier for explicit Qwen/OpenAI selection while keeping all Stage A validation offline.
- Committed Qwen Provider Stage A as `700dfee` (`feat: add offline Qwen provider support`).
- Completed the real Qwen pipeline over the Golden Repository: 19 real embeddings were stored through the existing pgvector index, a real query embedding retrieved the expected evidence at rank 1, `qwen3.7-flash` generated a grounded answer with two valid evidence references, and the backend resolved both citations.

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
- M5 `uv run pytest`: 43 passed, 6 live database tests skipped.
- M5 `RUN_DATABASE_TESTS=1 uv run pytest`: 49 passed, including repository-to-answer-to-real-citation and `/api/ask` coverage.
- M5 `uv run ruff check src tests migrations`: passed.
- Live OpenAI Responses call: not run because no `OPENAI_API_KEY` is configured; the official SDK contract is covered with a client fake.
- M6 `npm run build`: passed TypeScript project references and Vite production build (33 modules).
- M6 live browser/API/PostgreSQL workflow: ingested 78 accepted files, created 615 chunks, stored 615 vectors, ran independent retrieval, generated an answer, and resolved its citation.
- M6 responsive browser validation: desktop and 700px layouts rendered without horizontal overflow; browser console contained no warnings or errors.
- M7 exact-vector evaluation (8 queries, 19 chunks): Hit@1/Recall@1 0.7500, Hit@3/Recall@3 0.8750, Hit@5/Recall@5 1.0000, MRR@5 0.8375.
- M7 retained hybrid evaluation (same frozen dataset): Hit@1, Recall@1, Hit@3, Recall@3, Hit@5, Recall@5, and MRR@5 all 1.0000.
- M7 ordinary suite: 51 passed, 7 live database tests skipped; live suite: 59 passed; Ruff and frontend production build passed.
- Final clean migration validation used a new `repopilot_v1_validation_20260909a` database: upgrade base→`0004`, `alembic check`, downgrade to base, and second upgrade to `0004` all passed; the temporary database was removed afterward.
- Final clean-database checks: `uv sync --locked`, 59/59 backend tests, Ruff, Compose configuration, `npm ci` with 0 reported vulnerabilities, and the TypeScript/Vite production build all passed.
- Final evaluation rerun on the clean database reproduced the recorded 8-query vector and hybrid metrics and every expected first-relevant rank.
- Final clean-database browser pass: API/database health connected; 96 files produced 676 stored vectors; retrieval-only and answer endpoints returned HTTP 200; the answer citation focused its source card; browser console had no warnings/errors.
- Final Git/scope audit: eight ordered V1 milestone commits follow the Stage 0 baseline, no secret file is tracked, and no V2/later implementation signal was found.
- Live-provider verifier regression check: ordinary suite now has 52 passed / 8 live tests skipped; Ruff passes; the CLI exits before database access with a clear error when `OPENAI_API_KEY` is absent.
- Qwen Stage A focused provider/configuration suite: 27 passed using only fake clients; no external request or token usage occurred.
- Qwen Stage A ordinary suite: 66 passed, 8 database-only tests skipped; `uv run ruff check src tests migrations` passed.
- Qwen Stage A live-database suite: 74 passed after a clean Docker Desktop restart; `alembic current` confirmed `0004_add_vector_index (head)` and `alembic check` reported no new upgrade operations.
- Qwen Stage A Git/secret audit: `.env` remains ignored and untracked; `.env.example` contains an empty key placeholder; no real credential, authorization header, or secret logging was added; no migration, database schema, retrieval, evaluation dataset, Golden Repository, or frontend file changed.
- Qwen Stage B live verifier: `qwen3.7-text-embedding`, 8 accepted files, 19 chunks, 19 stored vectors, 512 dimensions for every vector, expected evidence at rank 1, `qwen3.7-flash`, 2 valid backend-resolved citations to `src/settings.py`.
- V1 final regression: ordinary backend suite 66 passed / 8 database tests skipped; live database suite 74 passed; Ruff passed; Alembic remained at `0004_add_vector_index` with no pending operations; frontend production build passed.
- V1 final evaluation rerun (8 queries, 19 chunks): vector Hit@1/Recall@1 0.7500, Hit@3/Recall@3 0.8750, Hit@5/Recall@5 1.0000, MRR@5 0.8375; hybrid returned 1.0000 for every reported metric.

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
- Select `gpt-5.6-luna` through the Responses API for cost-conscious external generation based on current official OpenAI documentation.
- Treat repository text only as delimited untrusted input; resolve model `[E#]` references against request context and never accept model-authored source metadata.
- Keep the UI evidence-first: retrieval remains callable without generation, and answer citations navigate to backend-derived evidence instead of hiding source selection.
- Retain the 70% exact-vector / 30% lexical rerank because it moved both observed bad cases to rank 1; keep the vector-only mode as the reproducible baseline.
- Use Alibaba Cloud Model Studio / Qwen as the actual V1 external provider: `qwen3.7-text-embedding` at 512 dimensions and `qwen3.7-flash` for grounded generation. OpenAI remains implemented and contract-tested, not live-tested.

## Actual Live Provider

- Provider: Alibaba Cloud Model Studio / Qwen, Beijing workspace.
- Embedding: `qwen3.7-text-embedding`, 512 dimensions.
- Generation: `qwen3.7-flash` through the OpenAI-compatible Responses API.

## Final Live Validation

- Real Embedding: PASS.
- Vector Dimension and pgvector Indexing: PASS (19/19 stored vectors at 512 dimensions).
- Real Query Embedding and Existing Retrieval: PASS (expected evidence rank 1).
- Existing Context Builder and untrusted-data boundary: PASS.
- Real Generation: PASS.
- Evidence Reference: PASS (2 valid references).
- Backend-resolved Citation: PASS (2 citations derived from request evidence).

## Blockers

- None.

## Remaining Work

- None within V1. Do not begin V2 without a separately authorized Version Goal.
