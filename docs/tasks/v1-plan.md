# RepoPilot V1 Execution Plan

## Goal

Deliver a debuggable, testable, evidence-grounded repository-level Codebase RAG product from local repository ingestion through inspectable React citations and measured retrieval quality.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| M0 — Foundation Check | Verify the Stage 0 application, database, migration, tests, and Git baseline; make only required reproducibility fixes | Complete |
| M1 — Repository Ingestion | Secure local repository registration, snapshots, scanning, filtering, and inspectable ingestion API | In progress |
| M2 — Code-aware Chunking | Structure-aware Python/TypeScript/JavaScript/TSX/JSX/Markdown chunks with bounded size and citation metadata | Not started |
| M3 — Embedding + Vector Index | Configured embeddings, migration-controlled pgvector storage, idempotent snapshot indexing, and exact vector search | Not started |
| M4 — Retrieval Engine | Independently callable, snapshot-scoped ranked evidence retrieval with explicit API contracts | Not started |
| M5 — RAG Generation + Citation | Bounded context builder, grounded generation, evidence-ID citations, and deterministic citation resolution | Not started |
| M6 — React Product UI | Local repository indexing and question workflow with answer, evidence, citations, and failure/loading states | Not started |
| M7 — Retrieval Quality Improvement / Evaluation | Golden repository, evaluation dataset, vector baseline metrics, evidence-based improvement decision, and recorded results | Not started |

## Current Milestone

M1 — Repository Ingestion.

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

## Validation Results

- `uv run pytest`: 9 passed, 1 database test skipped.
- `npm run build`: passed TypeScript and Vite production build.
- `docker compose config`: passed.
- `uv run alembic upgrade head` / `uv run alembic current`: passed at `0001_enable_pgvector`.
- `RUN_DATABASE_TESTS=1 uv run pytest`: 10 passed.
- `uv run ruff check src tests migrations`: passed.

## Important Decisions

- Preserve the Stage 0 synchronous FastAPI + SQLAlchemy architecture and database-only Compose boundary.
- Keep each V1 pipeline component explicit and injectable; do not introduce LangChain, LlamaIndex, agent loops, or speculative V2 structures.
- Use exact vector search as the mandatory first retrieval baseline; evaluate before retaining lexical or hybrid improvements.

## Blockers

- None.

## Remaining Work

- Execute M1–M7 in order.
