# RepoPilot V1 — Codebase RAG Goal

> Status: Ready to Start
>
> Version: V1 — Codebase RAG
>
> Depends on: Stage 0 — Project Inception
>
> Stage 0 status: Completed

---

# 1. Goal

Build the first real product version of RepoPilot:

a debuggable, testable, evidence-grounded repository-level Codebase RAG system.

V1 must allow a user to import a supported source-code repository, index its contents, ask questions about the codebase, retrieve relevant source chunks, generate an answer grounded in those chunks, and inspect the evidence used to produce the answer.

The target end-to-end product flow is:

```text
Repository
→ Snapshot
→ File Scan
→ File Filter
→ Parse
→ Code-aware Chunk
→ Embed
→ PostgreSQL + pgvector
→ Retrieve
→ Build Context
→ LLM
→ Answer
→ Source Citation
→ React Evidence UI
````

V1 is not an Agent system.

V1 is the foundation that later Agent versions will depend on.

---

# 2. Starting Point

Stage 0 has been completed.

The current engineering foundation already provides:

```text
React
→ HTTP
→ FastAPI
→ SQLAlchemy
→ PostgreSQL 17 + pgvector
```

Stage 0 also provides:

* React + TypeScript + Vite frontend
* FastAPI backend
* typed configuration
* root environment configuration
* PostgreSQL + pgvector through Docker Compose
* SQLAlchemy engine/session foundation
* Psycopg 3
* Alembic migrations
* backend/database health APIs
* backend tests
* opt-in live database integration tests
* frontend production build validation
* Git history and development documentation

V1 should extend this foundation.

Do not unnecessarily redesign Stage 0.

---

# 3. V1 Product Outcome

At V1 completion, a user should be able to:

1. provide a supported local source repository;
2. create a repository snapshot;
3. scan and filter relevant source files;
4. parse supported files;
5. generate code-aware chunks;
6. inspect chunk metadata;
7. generate embeddings for chunks;
8. persist indexed chunks and embeddings;
9. ask a natural-language question about the repository;
10. retrieve relevant code chunks;
11. inspect retrieval evidence independently of generation;
12. construct bounded LLM context from retrieved evidence;
13. generate an answer grounded in repository evidence;
14. receive citations pointing to real source locations;
15. inspect cited evidence in the React UI.

The system must make it possible to distinguish:

```text
Retrieval Error
```

from:

```text
Generation Error
```

This is a core V1 requirement.

---

# 4. V1 Milestones

The expected milestone structure is:

```text
M0 — Foundation Check
M1 — Repository Ingestion
M2 — Code-aware Chunking
M3 — Embedding + Vector Index
M4 — Retrieval Engine
M5 — RAG Generation + Citation
M6 — React Product UI
M7 — Retrieval Quality Improvement / Evaluation
```

Codex may decompose these milestones into smaller engineering tasks.

Codex may refine internal implementation details when necessary.

Codex must not change the V1 product scope or major architectural boundaries without escalation.

---

# 5. M0 — Foundation Check

Before implementing V1 functionality:

* inspect the completed Stage 0 architecture;
* inspect database configuration;
* inspect existing migrations;
* inspect tests;
* inspect Git history;
* confirm the working tree state;
* confirm PostgreSQL + pgvector are usable;
* identify only the minimum foundation changes required by V1.

Do not rebuild the Stage 0 foundation merely to make it look cleaner.

M0 should be small.

---

# 6. M1 — Repository Ingestion

## Goal

Safely turn a source-code repository into a versioned repository snapshot that RepoPilot can process.

Conceptual flow:

```text
Repository
→ Snapshot
→ File Scanner
→ File Filter
→ Accepted Files
```

---

## Repository

V1 should support a practical local repository ingestion workflow.

GitHub API integration is not part of V1.

Do not implement GitHub authentication or remote GitHub workflows.

---

## Repository Snapshot

Every indexed repository state must belong to a snapshot.

A snapshot represents one specific state of repository content.

The data model should make future mapping to a Git commit possible.

Do not assume repository content is permanently static.

---

## File Scanner

The scanner should recursively inspect repository files.

It must preserve repository-relative file paths.

---

## File Filtering

Default exclusions must include appropriate cases such as:

```text
.git
node_modules
dist
build
.venv
binary files
generated files
very large files
minified files
```

Sensitive files should be excluded by default, including appropriate patterns such as:

```text
.env
*.pem
*.key
credentials
secrets
```

Filtering rules must be independently testable.

---

## Initial Language Scope

V1 should primarily support:

* Python
* TypeScript
* JavaScript
* TSX
* JSX
* Markdown

Do not claim universal programming-language support.

---

# 7. M2 — Code-aware Chunking

## Goal

Convert accepted repository files into retrieval units that preserve useful code structure.

The baseline must use:

```text
semantic boundary
+
size constraint
```

---

## Preferred Semantic Boundaries

Where supported, chunking should prefer boundaries such as:

* class
* function
* method
* Markdown heading

A semantic unit must not automatically equal exactly one chunk.

Very large semantic units may be split further.

Very small units may remain separate initially unless measured retrieval quality justifies combining them.

---

## Parser Strategy

Use the simplest implementation that provides reliable semantic boundaries for the supported V1 languages.

Do not implement V2-level complete Code Intelligence.

Tree-sitter may be introduced if the current milestone genuinely requires it and the decision is justified.

Do not build:

* precise call graphs
* full reference graphs
* IDE-level semantic analysis

in V1.

---

## Chunk Metadata

Chunk data should preserve enough information to support retrieval, debugging, citation, and future re-indexing.

At minimum, consider:

* repository identifier
* snapshot identifier
* file path
* language
* chunk type
* symbol name
* qualified name where available
* parent symbol where available
* start line
* end line
* content hash
* chunking version

Do not invent metadata that has no current use.

---

## Raw Content vs Embedding Content

Keep these concepts separate:

```text
raw_content
```

and:

```text
embedding_content
```

`raw_content` represents the real source content.

`embedding_content` may include useful structural context such as:

```text
File Path
Symbol
Chunk Type
Source Content
```

Do not destroy the original source representation merely to improve embeddings.

---

# 8. M3 — Embedding + Vector Index

## Goal

Convert chunks into embeddings and persist them for retrieval.

Conceptual flow:

```text
Chunk
→ Embedding Content
→ Embedding API
→ Vector
→ PostgreSQL + pgvector
```

---

## Embedding Provider

Select an appropriate embedding model based on current:

* official documentation
* API availability
* embedding dimensions
* cost
* latency
* code retrieval suitability
* project simplicity

Record the selected model and relevant reasoning.

Do not hardcode embedding dimensions before the model is selected.

---

## Configuration

Embedding credentials must use environment variables.

Secrets must never be committed.

Update `.env.example` only with safe placeholders.

---

## Database

Introduce the V1 application tables through Alembic migrations.

Database design must support:

* repositories
* snapshots
* chunks
* embedding/vector storage
* retrieval metadata

Do not create speculative V2/V3 tables.

---

## Vector Search Baseline

Start with:

```text
Exact Vector Search
```

Do not initially introduce:

* HNSW
* IVFFlat
* ANN tuning

unless a measured requirement proves exact search impractical.

---

## Re-indexing

The design should avoid uncontrolled duplicate indexing.

Repository/snapshot/chunk identity and content hashes should support practical repeated indexing behavior.

Do not overengineer a distributed indexing system.

---

# 9. M4 — Retrieval Engine

## Goal

Given a question, return relevant repository chunks without generating an answer.

Conceptual interface:

```text
Question
→ Retriever
→ Ranked Evidence
```

Retriever must be an independently usable and testable component.

---

## Retriever Responsibilities

Retriever may handle:

* query embedding
* vector similarity search
* snapshot/repository scoping
* Top-K
* score/distance handling
* evidence result construction

Retriever must not:

* call the answer-generation LLM;
* generate final user-facing answers.

---

## Evidence

Retrieval results should include enough information for debugging.

At minimum:

* evidence/chunk ID
* file path
* symbol where available
* start line
* end line
* score or distance
* chunk content

---

## Snapshot Isolation

Queries for one snapshot must not accidentally retrieve chunks belonging to another repository or snapshot.

This must be tested.

---

## Retrieval Debugging

The retrieval layer must make it possible to inspect:

```text
Query
Top-K
Score / Distance
File
Symbol
Line Range
Chunk Content
```

Do not bury retrieval inside a single opaque RAG function.

---

# 10. M5 — Context Builder

## Goal

Transform retrieved evidence into bounded, structured context suitable for the LLM.

Context Builder must be an explicit component.

It should own responsibilities such as:

* evidence formatting
* ordering
* deduplication
* token/context budget
* evidence IDs
* bounded context construction

Do not implement context construction as only:

```python
"\n".join(chunks)
```

---

## Evidence IDs

Each piece of evidence included in the LLM context should have a stable evidence identifier for the current request.

Example concept:

```text
E1
E2
E3
```

These identifiers must map back to real retrieved chunks.

---

# 11. M5 — RAG Generation

## Goal

Generate answers based on retrieved repository evidence.

Conceptual flow:

```text
Question
→ Retriever
→ Evidence
→ Context Builder
→ LLM
→ Grounded Answer
```

---

## LLM Provider

Use an appropriate current LLM API.

Follow current official API documentation when implementing the integration.

Do not rely on obsolete tutorials when official API behavior differs.

Credentials must remain in environment variables.

---

## Grounding

The prompt should clearly instruct the model to answer from supplied repository evidence.

When evidence is insufficient:

the system should prefer expressing uncertainty rather than inventing repository facts.

---

# 12. Citation Architecture

Citation authenticity is a core V1 requirement.

The LLM must not invent:

* file paths
* line numbers
* symbols

as citation metadata.

Correct model:

```text
Retriever
→ Real Chunk IDs
→ Context Builder assigns Evidence IDs
→ LLM references Evidence IDs
→ Backend resolves IDs
→ Real File / Symbol / Lines / Content
```

Citation metadata must originate from repository/index data.

---

## Citation Output

User-visible citations should be able to resolve to:

* file path
* symbol where available
* start line
* end line
* source evidence

Citation mapping must be testable independently of the LLM's prose quality.

---

# 13. Repository Content Is Untrusted Data

Repository content must never automatically become trusted LLM instruction.

Treat repository content as:

```text
untrusted data
```

not:

```text
system instruction
```

Prompt construction must preserve this boundary.

Code or documentation containing text such as:

```text
Ignore previous instructions
```

must not automatically override application instructions.

V1 does not need to solve every prompt-injection problem.

It must establish the correct architectural boundary.

---

# 14. M6 — React Product UI

## Goal

Turn the V1 backend pipeline into an inspectable product.

RepoPilot should not look like only a generic chatbot.

The frontend should expose both:

```text
Answer
```

and:

```text
Evidence
```

---

## Required V1 UI Capabilities

The frontend should allow the user to perform the practical V1 workflow, including appropriate controls for:

* repository ingestion/indexing
* asking repository questions
* viewing answer state
* viewing retrieval evidence

Evidence presentation should include appropriate fields such as:

* File Path
* Symbol
* Line Range
* Score / Distance
* Chunk Content

When practical, citation interaction should let the user inspect the corresponding evidence.

---

## UI Boundary

Do not build the complete future V8 UI.

Do not prematurely implement:

* Agent traces
* patch editors
* test execution panels
* PR workflows
* MCP panels

V1 UI exists to prove and debug Codebase RAG.

---

# 15. M7 — Retrieval Quality Baseline

## Goal

Move from:

```text
"the demo seems to work"
```

to:

```text
"we can measure whether retrieval works"
```

---

## Golden Repository

Maintain a small controlled repository or fixture whose relevant files and symbols are known.

This repository should support repeatable retrieval evaluation.

---

## Evaluation Dataset

Create a small but meaningful V1 retrieval dataset.

Each evaluation case should contain something conceptually similar to:

```text
Query
Expected Evidence
```

Depending on implementation maturity, expected evidence may reference:

* file
* symbol
* chunk

---

## Baseline Metrics

Use appropriate retrieval metrics such as:

* Hit@K
* Recall@K
* MRR

Only use metrics actually implemented and correctly calculated.

Never fabricate numbers.

---

# 16. Retrieval Improvement Rule

V1 must first establish:

```text
Vector-only baseline
```

Only after real bad cases are observed may V1 experiment with improvements such as:

```text
Lexical Retrieval
Symbol Retrieval
Hybrid Retrieval
```

Any retained improvement should have evidence that it helps.

The workflow is:

```text
Baseline
→ Bad Case
→ Hypothesis
→ Implementation
→ Evaluation
→ Keep / Remove
```

Do not implement every advanced retrieval technique merely because it exists.

---

# 17. Testing Strategy

V1 must maintain tests throughout development.

Tests should cover appropriate levels.

---

## Unit Tests

Examples:

* file filtering
* language detection
* parser behavior
* chunking
* metadata generation
* content hashing
* context formatting
* citation mapping
* evaluation metric calculation

---

## Integration Tests

Examples:

```text
Repository
→ Scan
→ Chunk
→ Database
```

and:

```text
Chunk
→ Embedding
→ pgvector
→ Retrieval
```

Use real database integration where required.

---

## API Tests

Cover the V1 HTTP APIs introduced for:

* repositories
* indexing
* retrieval
* RAG/chat

Exact API design may be refined during implementation.

Keep contracts explicit.

---

## LLM / Embedding Tests

Do not make the entire ordinary test suite depend on paid external API calls.

Separate deterministic local tests from tests requiring:

* embedding API
* LLM API

External integration tests should be explicit and controlled.

Use mocks/fakes where they provide meaningful deterministic unit coverage.

Do not mock away the entire system and then claim end-to-end success.

---

# 18. V1 Observability Boundary

V1 does not require the full Production Observability stack.

However, core AI pipeline stages must be debuggable.

At minimum, developers should be able to determine:

```text
Repository ingestion result
Chunking result
Embedding/index result
Retrieval result
Context evidence
LLM result
Citation mapping
```

Do not require OpenTelemetry or production tracing unless a real V1 problem justifies it.

---

# 19. Performance Boundary

V1 should record practical performance where useful.

Possible measurements include:

* indexing duration
* number of accepted files
* number of chunks
* embedding calls
* retrieval latency
* LLM latency

Do not prematurely optimize.

Do not build large-scale distributed infrastructure.

---

# 20. Explicitly Forbidden V1 Scope

V1 must NOT implement:

* V2 full Code Intelligence
* complete AST reference graph
* precise call graph
* IDE-level semantic analysis
* autonomous repository Agent
* Agent Loop
* edit_file tool
* apply_patch tool
* run_tests Agent tool
* autonomous issue resolution
* multi-agent systems
* MCP
* GitHub API integration
* GitHub Issue workflow
* GitHub PR creation
* Agent sandbox
* authentication
* user accounts
* Redis
* distributed job queue
* production workers
* Kubernetes
* production deployment architecture
* production observability platform
* speculative scalability infrastructure

Do not scaffold empty modules for these capabilities.

---

# 21. Framework Boundary

Do not use LangChain or LlamaIndex to hide the V1 core pipeline.

The following must remain understandable and independently debuggable:

```text
Scanner
Filter
Parser
Chunker
Embedding Preparation
Vector Storage
Retriever
Context Builder
Citation Mapping
Generation
```

Official SDKs, database libraries, parsing libraries, and mature infrastructure libraries may be used where justified.

---

# 22. Security Boundary

V1 must at least consider:

* sensitive file exclusion
* path traversal
* malicious repository paths
* excessively large files
* binary files
* repository prompt injection
* secret leakage into LLM context

V1 does not execute arbitrary repository code.

Therefore a full Agent execution sandbox is not part of V1.

---

# 23. Database Migration Rule

All persistent V1 schema changes must use Alembic migrations.

Do not rely on undocumented manual SQL state.

A clean database should be able to reach the current V1 schema through migrations.

Existing Stage 0 migrations must remain valid.

---

# 24. Configuration Rule

All configurable external services must use typed environment configuration.

Examples may include:

* embedding API key
* embedding model
* LLM API key
* LLM model

Safe examples belong in `.env.example`.

Real secrets remain local and ignored.

---

# 25. Git Rule

Each meaningful V1 milestone should produce one or more clear commits.

Examples:

```text
feat: add repository ingestion pipeline

feat: implement code-aware chunking

feat: add embedding and vector indexing

feat: implement repository retrieval engine

feat: add grounded RAG generation and citations

feat: add retrieval evidence UI

eval: add V1 retrieval baseline
```

Do not wait until the entire V1 is finished and create one giant commit.

---

# 26. Execution Plan

Codex must create and maintain:

```text
docs/tasks/v1-plan.md
```

The plan should remain concise and contain:

* V1 goal
* milestones
* current milestone
* completed milestones
* validation results
* important implementation decisions
* blockers
* remaining work

It must reflect actual repository state.

It must not become a duplicate of this document.

---

# 27. Autonomous Execution

Within V1:

Codex may autonomously move between approved milestones.

Normal workflow:

```text
Inspect
→ Plan
→ Implement
→ Test
→ Self Review
→ Fix
→ Verify
→ Commit
→ Update Plan
→ Continue
```

Human approval is not required between ordinary V1 milestones.

Follow all escalation conditions defined in `AGENTS.md`.

---

# 28. Escalation

Stop and report when an `AGENTS.md` escalation condition applies.

V1-specific examples include:

* selected embedding model forces an architectural change;
* required external API credentials are unavailable;
* the proposed database schema conflicts with frozen architecture;
* parser strategy requires moving substantial V2 Code Intelligence into V1;
* tests cannot pass without expanding scope;
* a security issue makes the planned ingestion design unsafe;
* V1 requirements conflict materially with existing project documents.

Do not stop for routine implementation decisions.

---

# 29. V1 Final Acceptance Criteria

V1 is complete only when all applicable criteria below are satisfied.

## Repository Ingestion

* A supported repository can be ingested.
* Repository snapshots exist.
* File scanning works.
* filtering works.
* sensitive/irrelevant files are excluded.
* supported language scope is explicit.

## Chunking

* supported files produce code-aware chunks;
* semantic boundaries are used where appropriate;
* large units respect size constraints;
* required metadata exists;
* raw content and embedding content remain distinguishable.

## Embedding / Index

* embeddings can be generated through the configured provider;
* embeddings are stored through PostgreSQL + pgvector;
* application schema is migration-controlled;
* exact vector search works;
* repository/snapshot scope is preserved.

## Retrieval

* a question produces ranked repository evidence;
* retrieval can run independently of answer generation;
* evidence exposes source metadata;
* cross-repository/snapshot leakage is tested against.

## Context Builder

* context construction is explicit;
* evidence IDs exist;
* token/context limits are bounded appropriately;
* duplicated evidence is handled deliberately.

## Generation

* an LLM can answer repository questions using retrieved evidence;
* insufficient evidence does not silently become fabricated repository claims.

## Citation

* citations resolve from real evidence IDs;
* file paths and line ranges are backend/index derived;
* citation mapping is testable.

## Frontend

* the user can perform the V1 repository QA workflow;
* answers are visible;
* retrieval evidence is visible;
* source metadata is inspectable;
* failure/loading states are handled.

## Evaluation

* a Golden Repository or equivalent controlled fixture exists;
* a retrieval evaluation dataset exists;
* baseline retrieval metrics are calculated;
* actual measured results are recorded;
* no metric is fabricated.

## Engineering Quality

* relevant backend tests pass;
* relevant integration tests pass;
* frontend build passes;
* migrations apply correctly;
* important V1 behavior is documented;
* Git history contains meaningful milestone commits;
* V2 or later functionality has not been introduced.

---

# 30. Final V1 Validation

Before declaring V1 complete, run an end-to-end validation covering:

```text
Repository
→ Snapshot
→ Scan
→ Filter
→ Parse
→ Chunk
→ Embed
→ Store
→ Retrieve
→ Context
→ Generate
→ Cite
→ UI
```

Also verify independently:

```text
Question
→ Retriever
→ Evidence
```

without LLM generation.

Validate a clean/reproducible database migration path.

Run the V1 retrieval evaluation dataset and record actual results.

Review:

* final architecture
* final diff
* dependencies
* database schema
* migrations
* tests
* evaluation
* Git history
* documentation
* known limitations
* security boundaries
* forbidden-scope compliance

---

# 31. Completion Report

When V1 is complete, provide a final report containing:

## Milestones

List completed M0–M7 milestones.

## Final Architecture

Describe major V1 modules and responsibilities.

## Index Pipeline

Describe:

```text
Repository
→ Index
```

## Query Pipeline

Describe:

```text
Question
→ Answer + Evidence
```

## Database

Describe tables, relationships, migrations, and vector storage.

## Models / External APIs

Document actual embedding and LLM models used.

## Validation

List commands actually executed and results.

## Evaluation

Report actual measured retrieval metrics and dataset size.

Do not fabricate missing results.

## Git

List meaningful milestone commits.

## Limitations

State concrete V1 limitations.

## Risks

State remaining architecture, retrieval, cost, security, or maintenance risks.

## Scope Check

Confirm whether any V2 or later functionality was introduced.

---

# 32. Version Boundary

When all V1 acceptance criteria are satisfied:

```text
V1 Final Validation
→ Completion Report
→ STOP
```

Do not begin:

```text
V2 — Code Intelligence
```

automatically.

Starting V2 requires a new explicitly active Version Goal.

---

# 33. Final Principle

V1 is successful only if RepoPilot can answer:

```text
"Why did the system choose this code as evidence?"
```

and the developer can inspect the answer.

The target is not merely:

```text
LLM produced a plausible response.
```

The target is:

```text
Repository
→ Explicit Indexing
→ Observable Retrieval
→ Controlled Context
→ Grounded Generation
→ Real Citation
→ Measured Retrieval Quality
```

That is the V1 Codebase RAG baseline.

````
