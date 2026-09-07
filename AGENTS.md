# AGENTS.md

## Project Mission

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

For the complete long-term project scope and architecture roadmap, read:

`docs/PROJECT.md`

---

## Current Stage

Current stage:

**Stage 0 — Project Inception**

The current goal is to establish the project foundation and the first working application path.

Initial application flow:

Browser
→ React
→ HTTP
→ FastAPI
→ JSON Response
→ React UI

Later Stage 0 tasks will introduce PostgreSQL and pgvector infrastructure.

Do not implement future functionality before the corresponding task explicitly requires it.

---

## Task Source of Truth

Engineering work must be driven by explicit task files under:

`docs/tasks/`

Before making changes:

1. Read this `AGENTS.md`.
2. Read `docs/PROJECT.md` when architectural context is needed.
3. Read the current task file completely.
4. Only implement functionality required by the current task.

If the task conflicts with this file or the project architecture, stop and report the conflict instead of silently changing the architecture.

Do not expand scope based on assumptions about future RepoPilot requirements.

---

## Repository Architecture

Current top-level structure:

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
```

### `apps/web`

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

Frontend components should not contain backend implementation logic.

HTTP calls should be isolated in appropriate API modules instead of being duplicated throughout UI components.

---

### `apps/api`

Backend application.

Technology:

* Python 3.13
* FastAPI
* uv
* pytest

Responsibilities:

* HTTP API
* input validation
* application orchestration
* future integration with database and AI capabilities

HTTP routes should remain thin.

Business or domain logic should not be unnecessarily embedded directly inside route handlers once that logic becomes substantial.

Do not create abstractions before they have a concrete responsibility.

---

### `docs`

Contains project documentation that has real engineering value.

Important files:

* `docs/PROJECT.md` — long-term project charter and roadmap
* `docs/tasks/` — explicit engineering task specifications

Do not create documentation merely for appearance or process overhead.

---

## Architecture Rules

Follow these rules unless a task explicitly changes them.

1. Keep frontend and backend clearly separated.

2. Keep modules focused on one concrete responsibility.

3. Prefer simple architecture over speculative abstractions.

4. Do not create directories or modules for features that do not exist yet.

5. Dependencies must solve a current engineering problem.

6. Do not introduce technology only because it may be useful later.

7. Preserve explicit data flow and module boundaries.

8. Core AI functionality must eventually remain independently debuggable.

9. Avoid hidden framework magic around important RepoPilot behavior.

10. Do not perform unrelated refactors while completing a scoped task.

11. Avoid large cross-cutting changes unless the task explicitly requires them.

12. Prefer small, reviewable, testable changes.

---

## Current Forbidden Scope

Unless the current task explicitly introduces one of these capabilities, do NOT implement or scaffold:

* repository ingestion
* repository scanning
* repository snapshots
* code parsing
* AST processing
* Tree-sitter
* chunking
* embeddings
* embedding APIs
* vector indexing
* pgvector application logic
* retrieval
* semantic search
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
* code modification agents
* MCP
* GitHub integration
* authentication
* Redis
* queues
* workers
* background jobs
* caching infrastructure
* observability platforms
* production deployment architecture
* Kubernetes
* multi-agent systems

Do not create empty placeholder modules for these features.

They will be introduced only when RepoPilot reaches the appropriate milestone.

---

## Coding Rules

### General

* Keep code readable and explicit.
* Prefer straightforward implementation over clever implementation.
* Avoid premature optimization.
* Avoid speculative abstractions.
* Avoid unnecessary dependencies.
* Do not duplicate logic unnecessarily.
* Keep changes limited to the current task.
* Do not silently change architecture decisions.

---

### Python

* Use type hints for application code.
* Use clear function and variable names.
* Keep modules focused.
* Follow standard Python conventions.
* Avoid unnecessary inheritance or design patterns.
* Avoid global mutable application state unless technically justified.
* Prefer explicit dependencies and data flow.

Do not introduce complex architecture patterns merely to make the project look enterprise-grade.

---

### TypeScript

* Do not use `any` unless there is a concrete justification.
* Define interfaces/types for API boundaries.
* Keep HTTP communication separated from presentational UI where practical.
* Keep React state ownership clear.
* Avoid unnecessary global state.
* Do not add a state-management library unless a real requirement appears.
* Do not add a UI component library unless explicitly required.

---

## API Rules

API paths should use a consistent prefix:

```text
/api/
```

Examples:

```text
GET /api/health
```

API contracts should be explicit.

When frontend and backend exchange structured data:

* define the backend response clearly
* define the corresponding TypeScript type
* avoid relying on undocumented response shapes

Do not introduce versioned APIs such as `/api/v1` until there is an actual versioning requirement.

---

## Configuration and Secrets

Secrets must never be committed to Git.

Never hardcode:

* API keys
* database passwords
* GitHub tokens
* private credentials
* production secrets

Use environment variables when configuration becomes necessary.

Commit example configuration files such as:

```text
.env.example
```

Do not commit:

```text
.env
```

All example values must be non-sensitive placeholders.

---

## Dependency Rules

Before adding a dependency, verify that:

1. the current task actually requires it;
2. the standard library or existing dependency cannot reasonably solve the problem;
3. the dependency has a clear responsibility.

Do not add dependencies for hypothetical future use.

For core RepoPilot logic, prefer explicit implementation over frameworks that hide important behavior.

In particular, do not introduce LangChain or LlamaIndex during the early baseline stages unless a future task explicitly approves them.

---

## Testing Rules

Every engineering task must run the tests and validation commands relevant to the changed code.

### Backend

From `apps/api`:

```bash
uv run pytest
```

When applicable, also verify that the FastAPI application can start successfully.

---

### Frontend

From `apps/web`:

```bash
npm run build
```

Run any additional configured lint or test commands when they exist.

---

### General

Do not claim that a task is complete if relevant tests fail.

If a test cannot be executed:

* explain exactly why;
* state which validation was not performed;
* do not report it as passing.

When fixing a bug, add or update a test when practical so the same regression can be detected later.

---

## Git Rules

Keep commits small and meaningful.

Commit messages should describe the engineering change.

Preferred examples:

```text
feat: initialize RepoPilot application foundation

feat: add PostgreSQL development infrastructure

test: add backend health endpoint coverage

fix: prevent invalid health response state
```

Avoid meaningless messages such as:

```text
update
fix
changes
final
test123
```

Do not rewrite unrelated Git history.

Do not combine unrelated work into the same commit when it can reasonably be separated.

---

## Documentation Rules

Documentation must reflect the actual system.

Do not claim that RepoPilot supports functionality that has not been implemented.

Always distinguish:

* current functionality
* planned functionality

Update documentation when a task materially changes:

* architecture
* local development commands
* configuration
* module responsibilities
* important technical decisions

Do not generate large amounts of redundant documentation.

---

## Engineering Decision Rule

Before introducing a new technology or architectural layer, answer:

1. What real problem does it solve?
2. Why is it needed now?
3. What happens if we do not use it?
4. Is there a simpler solution?
5. Is the added complexity justified?

If these questions cannot be answered clearly, do not introduce the technology yet.

RepoPilot development follows:

Baseline
→ Observe failures / bad cases
→ Propose improvement
→ Implement
→ Evaluate
→ Keep or remove

Do not add complexity only because a technique appears more advanced.

---

## Scope Discipline

A task specification defines the allowed scope.

Do not:

* implement adjacent features because they seem easy;
* prepare speculative future architecture;
* refactor unrelated modules;
* add unused dependencies;
* create future directories;
* change technology choices without explaining why.

If completing the task exposes a necessary architectural change that is outside scope:

1. do not silently implement it;
2. document the issue;
3. propose the change in the completion report.

---

## Completion Requirements

After completing a coding task, provide a concise report containing:

### Files Changed

List created, modified, or deleted files.

### Implementation

Explain what was implemented.

### Architecture

Explain any relevant module or data-flow changes.

### Dependencies

List new dependencies and why they were required.

### Validation

List commands actually executed and their results.

### Remaining Issues

State known limitations, failures, or unfinished work.

### Risks

Identify anything that could create future maintenance or architectural problems.

### Scope Check

Explicitly state whether anything outside the task scope was introduced.

Do not continue automatically into the next milestone or task.

Wait for review before expanding scope.
