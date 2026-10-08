# AGENTS.md

## 1. Project Mission

RepoPilot is a long-term AI Codebase Intelligence & Issue Resolution Agent.

The project will evolve incrementally through:

Codebase RAG
→ Code Intelligence
→ Repository Agent
→ Issue Resolution
→ MCP / GitHub Integration
→ Evaluation
→ Production Engineering

The goal is to build a real, explainable, testable AI engineering system rather than a collection of disconnected demos.

RepoPilot must evolve incrementally.

Do not implement future capabilities merely because they may eventually be useful.

For the complete long-term product scope, architecture direction, and version roadmap, read:

`docs/PROJECT.md`

---

## 2. Current Stage

Current stage:

**V1 — completed**

Stage 0 — Project Inception has been completed and serves as the stable engineering foundation.

V1 has been establish:

- repository ingestion
- repository snapshots
- file scanning and filtering
- code-aware chunking
- embedding generation
- PostgreSQL + pgvector indexing
- retrieval
- context building
- LLM generation
- source citation
- retrieval evidence UI
- retrieval evaluation

V1 must follow the baseline-first architecture defined in `docs/PROJECT.md`.

Do not implement V2 Code Intelligence, Agent, MCP, GitHub integration, or later-stage functionality unless explicitly authorized by a later goal.
---

## 3. Documentation Hierarchy

RepoPilot uses several different kinds of project documents.

Their responsibilities must remain distinct.

### `AGENTS.md`

Defines:

- engineering operating rules
- architecture constraints
- coding rules
- testing rules
- Git rules
- scope discipline
- autonomous execution behavior
- escalation conditions

This file controls how Codex works inside the repository.

---

### `docs/PROJECT.md`

Defines:

- long-term product scope
- architecture direction
- version roadmap
- major technical principles
- product boundaries
- evaluation philosophy
- security principles
- portfolio and interview goals

This is the long-term project charter.

---

### Goal Specifications

Version-level, stage-level, or milestone-level goals define:

- what outcome must be achieved
- allowed scope
- architecture boundary
- acceptance criteria
- forbidden scope

A goal may cover multiple engineering milestones.

---

### `docs/tasks/`

Contains:

- historical scoped task specifications
- Codex-maintained execution plans
- implementation progress when needed

Completed task specifications are historical records.

A completed task must not be treated as the active task unless explicitly instructed.

Execution plans describe how to achieve a goal.

They do not override:

1. `AGENTS.md`
2. `docs/PROJECT.md`
3. the active goal specification

---

## 4. Work Source of Truth

RepoPilot supports two engineering execution modes.

### Mode A — Scoped Task

Use for:

- bug fixes
- small features
- isolated refactors
- narrow engineering changes

A scoped task should normally define:

- Goal
- Context
- Scope
- Requirements
- Constraints
- Acceptance Criteria
- Tests

---

### Mode B — Autonomous Goal

Use for:

- Stage completion
- Version implementation
- larger milestones
- work containing several dependent engineering steps

For larger goals, Codex may autonomously:

Goal
→ inspect repository
→ create implementation plan
→ decompose milestones
→ implement
→ test
→ self-review
→ fix
→ verify
→ commit
→ continue

Human-written individual task files are not required for every internal engineering step.

The important requirement is that the resulting work remains:

- scoped
- understandable
- testable
- reviewable
- recoverable through Git

---

## 5. Before Making Changes

Before starting engineering work:

1. Read this `AGENTS.md`.
2. Read `docs/PROJECT.md`.
3. Read the active goal or task specification, if one exists.
4. Inspect the current repository.
5. Inspect relevant existing code before modifying it.
6. Inspect relevant Git history when previous architectural decisions matter.
7. Determine what has already been completed.
8. Avoid reimplementing completed work without a concrete reason.

For larger goals:

9. Create or update an execution plan under `docs/tasks/`.
10. Break the goal into logical milestones before large-scale implementation.

If project documents conflict in a way that affects architecture or scope:

**stop and report the conflict instead of guessing.**

---

## 6. Repository Architecture

Current top-level architecture:

```text
RepoPilot/
├── apps/
│   ├── web/
│   └── api/
├── docs/
│   ├── PROJECT.md
│   └── tasks/
├── AGENTS.md
├── README.md
└── .gitignore
````

Additional directories should only be introduced when an active milestone creates a real responsibility for them.

Do not create speculative future directories.

---

## 7. `apps/web`

Frontend application.

Technology:

* React
* TypeScript
* Vite
* npm

Responsibilities:

* user interface
* browser-side state
* calling RepoPilot backend APIs
* rendering backend responses
* later visualization of retrieval evidence and agent execution state

Frontend components should not contain backend implementation logic.

HTTP communication should be isolated in appropriate API modules rather than duplicated throughout UI components.

Keep React state ownership clear.

Do not introduce global state management until actual application complexity requires it.

Do not add a UI component framework unless an active goal requires one.

---

## 8. `apps/api`

Backend application.

Technology:

* Python 3.13
* FastAPI
* uv
* pytest

Responsibilities:

* HTTP API
* request validation
* application orchestration
* database access
* later AI application capabilities

HTTP routes should remain thin.

Once logic becomes substantial, route handlers should delegate to modules with clear responsibilities.

Do not create repository/service/domain abstractions merely because such patterns are common in enterprise projects.

Create abstractions only when real code responsibility requires them.

---

## 9. Infrastructure

Stage 0 may use Docker Compose for local infrastructure.

Current intended use:

Docker Compose
→ PostgreSQL
→ pgvector extension

This exists to provide reproducible local database infrastructure.

Stage 0 does **not** imply that the entire application should be containerized.

Unless explicitly required by a later goal, do not prematurely introduce:

* Dockerized React
* Dockerized FastAPI
* production container architecture
* Kubernetes
* orchestration platforms

Docker-based sandboxing for Agent code execution belongs to a later stage.

---

## 10. Architecture Rules

Follow these rules unless an explicitly approved architectural decision changes them.

1. Keep frontend and backend clearly separated.

2. Keep modules focused on concrete responsibilities.

3. Prefer simple architecture over speculative architecture.

4. Do not create modules for functionality that does not yet exist.

5. Dependencies must solve a current engineering problem.

6. Do not introduce technology only because it may be useful later.

7. Preserve explicit request flow and data flow.

8. Important AI pipeline components must remain independently debuggable.

9. Avoid framework abstractions that hide core RepoPilot behavior.

10. Avoid large unrelated refactors.

11. Prefer small, reviewable engineering changes inside larger goals.

12. Preserve stable interfaces once dependent modules begin using them.

13. Do not silently change frozen technology or architecture decisions.

14. If a simpler solution satisfies the current requirement, prefer it.

15. Do not optimize hypothetical bottlenecks.

---

## 11. Current Forbidden Scope

Unless the active goal or milestone explicitly introduces one of these capabilities, do NOT implement or scaffold:

* repository ingestion
* repository scanning
* repository snapshots
* code parsing
* AST processing
* Tree-sitter
* code-aware chunking
* embeddings
* embedding APIs
* vector indexing application logic
* retrieval
* semantic search
* lexical search
* hybrid search
* symbol search
* RAG
* context builders
* source citations
* LLM integration
* LangChain
* LlamaIndex
* agent loops
* tool calling
* repository modification agents
* MCP
* GitHub integration
* authentication
* Redis
* job queues
* background workers
* caching infrastructure
* production observability platforms
* production deployment architecture
* Kubernetes
* multi-agent systems

Stage 0 may introduce:

* PostgreSQL
* pgvector database extension
* SQLAlchemy
* PostgreSQL driver
* Alembic
* environment configuration
* Docker Compose for local database infrastructure

Do not create empty placeholder modules for future AI features.

---

## 12. Baseline-First Rule

RepoPilot follows:

Baseline
→ Observe failures / bad cases
→ Propose improvement
→ Implement
→ Evaluate
→ Keep or remove

Examples:

Do not implement Hybrid Retrieval simply because it sounds more advanced.

First establish Vector Retrieval.

Then identify bad cases.

Then evaluate whether lexical or symbol retrieval actually improves the system.

Likewise:

Do not introduce HNSW merely because approximate search is common.

Start with exact vector search.

Optimize only when measured scale or latency justifies it.

---

## 13. Core AI Framework Rule

During early RepoPilot baseline development, do not introduce frameworks such as:

* LangChain
* LlamaIndex

to hide core project behavior unless a future goal explicitly approves them.

Core components such as:

* repository scanning
* parsing
* chunking
* embedding preparation
* retrieval
* context construction
* citation mapping
* agent tool interfaces

should remain understandable and independently debuggable.

Using mature infrastructure libraries and official SDKs is allowed when they solve a concrete problem.

---

## 14. Coding Rules

### General

* Keep code readable and explicit.
* Prefer straightforward implementation over clever implementation.
* Avoid premature optimization.
* Avoid speculative abstractions.
* Avoid unnecessary dependencies.
* Avoid unnecessary duplication.
* Keep changes limited to the active goal or current milestone.
* Do not perform unrelated cleanup while implementing scoped work.
* Do not silently change architecture.
* Prefer code that can be tested independently.
* Remove dead code instead of preserving unused speculative code.

---

## 15. Python Rules

* Use type hints for application code.
* Use clear function and variable names.
* Keep modules focused.
* Follow standard Python conventions.
* Prefer explicit dependencies and data flow.
* Avoid unnecessary inheritance.
* Avoid unnecessary design patterns.
* Avoid global mutable application state unless technically justified.
* Prefer deterministic functions where practical.
* Separate I/O-heavy behavior from pure transformation logic when useful for testing.

Do not make the backend appear enterprise-grade by introducing architectural layers that have no real responsibility.

---

## 16. TypeScript Rules

* Do not use `any` unless there is a concrete documented reason.
* Define types/interfaces at API boundaries.
* Keep HTTP communication separated from presentation logic where practical.
* Keep React state ownership explicit.
* Avoid unnecessary global state.
* Do not add state-management libraries without real need.
* Do not add UI libraries unless explicitly required.
* Prefer explicit error states for backend communication.

---

## 17. API Rules

Use a consistent backend API prefix:

```text
/api/
```

Example:

```text
GET /api/health
```

Do not introduce `/api/v1` until actual API versioning is required.

API contracts must be explicit.

When frontend and backend exchange structured data:

* define backend response structure
* define corresponding TypeScript types
* avoid undocumented response fields
* avoid silently changing API contracts

Breaking API changes must update dependent frontend code and tests together.

---

## 18. Database Rules

Database schema changes must be reproducible.

Once migrations are introduced:

* use migrations for schema evolution
* do not rely on undocumented manual database edits
* keep migration history meaningful
* verify migrations on the intended development database

Stage 0 should only establish database foundation.

Do not create future V1 embedding/vector schemas until the relevant V1 milestone defines:

* embedding provider/model
* embedding dimensions
* chunk schema
* indexing requirements

pgvector may be enabled as a PostgreSQL extension before vector application tables exist.

---

## 19. Configuration and Secrets

Secrets must never be committed to Git.

Never hardcode:

* API keys
* database passwords
* GitHub tokens
* private credentials
* production secrets

Use environment variables.

Commit safe configuration templates such as:

```text
.env.example
```

Do not commit:

```text
.env
```

Example files must contain placeholders rather than real credentials.

Configuration should fail clearly when required values are missing.

---

## 20. Dependency Rules

Before adding a dependency, verify:

1. the current goal actually needs it;
2. existing code or the standard library cannot reasonably solve the problem;
3. the dependency has one concrete responsibility;
4. the dependency does not unnecessarily hide important RepoPilot behavior.

Do not add dependencies for hypothetical future functionality.

If a dependency is added, include its purpose in the completion report.

---

## 21. Testing Rules

Every engineering milestone must run validation relevant to the code changed.

Do not claim success if relevant tests fail.

If validation fails:

diagnose
→ fix
→ run again

Continue until:

* all required checks pass, or
* a genuine blocker is identified

If a validation command cannot be executed:

* state exactly why
* state which check was not performed
* do not report it as passing

---

## 22. Backend Validation

From:

`apps/api`

Primary test command:

```bash
uv run pytest
```

When relevant, also verify:

* FastAPI application startup
* API behavior
* database connectivity
* migrations
* integration tests

Do not substitute manual observation for automated tests when a practical automated test can be written.

---

## 23. Frontend Validation

From:

`apps/web`

Primary validation command:

```bash
npm run build
```

Also run configured:

* lint
* tests
* type checks

when they exist and are relevant.

Development-mode success alone is not sufficient if the production build fails.

---

## 24. Database Validation

When database infrastructure or migrations change, validate as appropriate:

* database container starts
* PostgreSQL becomes ready
* pgvector extension is available when required
* migrations apply successfully
* application can connect using configured environment variables
* migration state is reproducible from a clean database when practical

Do not report database work as complete based only on configuration files.

---

## 25. Bug Fix Rule

When fixing a bug:

1. reproduce or clearly identify the failure;
2. determine the root cause;
3. implement the smallest reasonable fix;
4. add or update a regression test when practical;
5. run relevant validation again.

Avoid unrelated refactors during bug fixing.

---

## 26. Git Rules

Keep Git history meaningful.

Prefer small commits corresponding to real engineering changes.

Good examples:

```text
feat: initialize RepoPilot application foundation

feat: add PostgreSQL development infrastructure

feat: add database migration foundation

test: add database integration coverage

fix: prevent invalid backend health state
```

Avoid:

```text
update

fix

changes

final

final2

test123
```

Do not rewrite unrelated Git history.

Do not combine unrelated engineering work into the same commit when separation is reasonable.

A larger autonomous goal should normally produce several meaningful milestone commits rather than one giant final commit.

---

## 27. Documentation Rules

Documentation must describe the actual system.

Always distinguish:

* implemented functionality
* planned functionality

Update documentation when engineering work materially changes:

* architecture
* local setup
* dependencies
* configuration
* database setup
* development commands
* API behavior
* module responsibilities
* important technical decisions

Do not generate documentation merely to make the repository look professional.

Prefer a small set of accurate documents over a large set of stale documents.

---

## 28. Engineering Decision Rule

Before introducing a new technology or architectural layer, answer:

1. What real problem does it solve?
2. Why is it needed now?
3. What happens if we do not use it?
4. Is there a simpler solution?
5. Is the added complexity justified?

If these questions cannot be answered clearly:

do not introduce the technology yet.

---

## 29. Scope Discipline

The active goal or task specification defines the allowed scope.

Do not:

* implement adjacent features merely because they are easy;
* prepare speculative future architecture;
* refactor unrelated modules;
* add unused dependencies;
* create future feature directories;
* change technology choices silently;
* cross into the next product version without authorization.

If completing the current milestone exposes a necessary architectural change outside scope:

1. do not silently implement the change;
2. document the problem;
3. explain the impact;
4. stop if the decision meets an escalation condition.

---

## 30. Autonomous Execution and Self-Validation

For version-level, stage-level, or milestone-level goals, Codex may autonomously decompose the goal into smaller engineering tasks.

Before declaring any milestone complete:

1. Re-read the relevant goal and acceptance criteria.
2. Review the implementation against every requirement.
3. Run all relevant tests, builds, type checks, migrations, and validation commands.
4. If validation fails:

   * diagnose the failure;
   * fix the implementation;
   * run validation again.
5. Repeat until all required checks pass or a genuine blocker is identified.
6. Review the final diff for:

   * scope violations;
   * unnecessary changes;
   * unused dependencies;
   * speculative abstractions;
   * duplicated logic;
   * dead code;
   * obvious maintainability problems.
7. Verify acceptance criteria explicitly.
8. Create a meaningful Git commit when Git operations are available.
9. Update the execution plan.
10. Continue to the next milestone when continuation conditions are satisfied.

Do not declare success merely because code was written.

---

## 31. Milestone Execution

For larger goals, use this loop:

Goal
→ Inspect Repository
→ Create / Update Execution Plan
→ Select Current Milestone
→ Implement
→ Test
→ Self Review
→ Fix
→ Verify Acceptance Criteria
→ Commit
→ Update Plan
→ Continue

Normal milestone boundaries do not require human approval.

Codex may continue autonomously when:

* the architecture remains consistent with `docs/PROJECT.md`;
* the active goal clearly permits the next milestone;
* required validation passes;
* no frozen architectural decision must change;
* no escalation condition exists.

---

## 32. Escalation Conditions

Codex must stop and report instead of guessing when:

* project documents materially conflict;
* a major architecture change is required;
* a frozen technology choice must be changed;
* the active goal is ambiguous in a way that affects system architecture;
* required credentials or permissions are unavailable;
* validation cannot pass without changing scope;
* implementation exposes a design flaw likely to cause substantial rework;
* a destructive operation requires approval;
* a security-sensitive action requires approval;
* important user data may be destroyed;
* Git history would need destructive rewriting;
* proceeding would cross into a later Version that has not been authorized.

Do not stop for routine implementation decisions that can be safely resolved within existing architecture rules.

---

## 33. Progress Persistence

For long-running goals, maintain a concise execution plan inside the repository.

Recommended location:

```text
docs/tasks/
```

The plan should record:

* goal
* milestones
* current milestone
* completed milestones
* validation results
* important implementation decisions
* blockers
* remaining work

The plan exists so progress does not depend entirely on conversation history.

Keep it concise.

Do not turn the execution plan into a second `PROJECT.md`.

Do not use progress documentation as a substitute for:

* tests
* Git commits
* working code

---

## 34. Completion Report

After completing a scoped task, milestone, stage, or version, provide a concise completion report.

Include:

### Files Changed

List important created, modified, or deleted files.

### Implementation

Explain what was implemented.

### Architecture

Explain relevant architecture or data-flow changes.

### Dependencies

List new dependencies and why they were required.

### Validation

List commands actually executed and their results.

### Git

List meaningful commits created during the work when available.

### Remaining Issues

State known limitations, failures, or unfinished work.

### Risks

Identify concrete maintenance, architecture, security, or compatibility risks.

### Scope Check

Explicitly state whether anything outside the active goal was introduced.

Do not conceal failed validation.

---

## 35. Version Boundary

Completing milestones inside a Stage or Version may happen autonomously.

Crossing from one major Stage / Version into another may not.

Examples:

Stage 0
→ V1

V1
→ V2

V2
→ V3

These transitions require an explicitly active new goal.

Therefore:

When Stage 0 is complete:

* perform final Stage 0 validation;
* produce the completion report;
* stop.

Do not begin V1 automatically.

When V1 is complete:

* perform final V1 validation;
* produce the completion report;
* stop.

Do not begin V2 automatically.

---

## 36. Learning Boundary

Codex is responsible for engineering execution.

It does not need to stop between normal milestones solely to teach the implementation.

Human learning and engineering execution are separate workflows.

For important modules, the project owner must eventually be able to explain:

* what the module is;
* why it exists;
* its inputs;
* its outputs;
* who calls it;
* what it calls;
* where data goes next;
* where failures can occur;
* how to debug it;
* why this design was chosen over alternatives.

The fact that Codex successfully implemented a module does not automatically mean the project owner understands it.

Engineering work may continue autonomously.

Learning review can occur at:

* important architecture checkpoints;
* user-requested learning sessions;
* version completion review.

---

## 37. Final Principle

RepoPilot is a product and engineering project, not a technology checklist.

Every meaningful addition should provide at least one of:

* real product capability;
* measurable engineering improvement;
* improved reliability;
* improved debuggability;
* improved safety;
* evidence of job-relevant engineering ability.

If a feature provides none of these:

do not build it.


