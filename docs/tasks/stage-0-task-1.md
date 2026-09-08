# RepoPilot — Stage 0 Task 1
> Status: Completed
>
> Completed as part of Stage 0 — Project Inception.
>
> This file is a historical specification for the completed Stage 0 Task 1.
> It must not be treated as the active task unless explicitly instructed.
>
> Future Stage 0 work is driven by the active Stage 0 goal and its execution plan.
## Goal

Initialize the RepoPilot repository and establish the first working application path:

React frontend
→ HTTP request
→ FastAPI backend
→ JSON response
→ React UI

This task is only the initial project foundation.

Do NOT implement repository ingestion, RAG, embeddings, pgvector, agents, MCP, GitHub integration, or any later-stage functionality.

---

## Context

RepoPilot is a long-term AI Codebase Intelligence & Issue Resolution Agent.

The project will eventually evolve through:

Codebase RAG
→ Code Intelligence
→ Repository Agent
→ Issue Resolution
→ MCP / GitHub
→ Evaluation
→ Production Engineering

We are currently at:

Stage 0 — Project Inception.

This task establishes the repository structure and the first frontend/backend communication loop.

---

## Current Architecture

The repository is currently empty or contains no meaningful application architecture.

Target structure for this task:

RepoPilot/
├── apps/
│   ├── web/
│   └── api/
├── docs/
├── AGENTS.md
├── README.md
└── .gitignore

Do not create future directories such as:

rag/
agent/
mcp/
retrieval/
embedding/
chunking/
workers/

They do not belong to the current stage.

---

## Technology

Frontend:

* React
* TypeScript
* Vite
* npm

Backend:

* Python 3.13
* FastAPI
* uv
* pyproject.toml

Testing:

* pytest for backend

Do not introduce additional frameworks unless required for this task.

---

## Scope

Implement only:

1. Repository directory structure
2. React + TypeScript frontend
3. FastAPI backend
4. Backend health endpoint
5. Frontend call to backend health endpoint
6. Minimal CORS configuration for local development
7. Basic backend API test
8. Root AGENTS.md
9. Basic README
10. Appropriate .gitignore files

---

## Backend Requirements

Create a Python package under:

apps/api/src/repopilot/

The FastAPI application must expose:

GET /api/health

Example response:

{
"status": "ok",
"service": "repopilot-api"
}

Keep HTTP routing separated from the FastAPI application entry point.

Suggested responsibility:

main.py

* create/configure FastAPI application
* register routers
* configure CORS

api/routes/health.py

* health endpoint

Do not add database code yet.

Do not add service/repository abstractions that currently have no real responsibility.

---

## Frontend Requirements

Create a React + TypeScript application under:

apps/web/

The frontend must call:

GET http://localhost:8000/api/health

Do not place the fetch request directly throughout UI components.

Create a small API module such as:

src/api/health.ts

The UI should clearly display one of these states:

* checking backend
* backend connected
* backend unavailable

Keep the UI extremely simple.

This task is not a design task.

Do not install a UI component library.

---

## Data Flow

Browser

→ React App

→ health API client

→ HTTP GET /api/health

→ FastAPI

→ health route

→ JSON response

→ frontend API client

→ React state

→ rendered UI

---

## Interfaces

Backend:

GET /api/health

Response:

{
"status": "ok",
"service": "repopilot-api"
}

Frontend:

Provide a typed function similar in responsibility to:

getHealth()

It should return typed health response data.

Do not use `any`.

---

## CORS

Allow the local Vite development origin required for this project.

Do not configure permissive production-style:

Access-Control-Allow-Origin: *

unless technically necessary and explicitly explained.

---

## AGENTS.md

Create a root AGENTS.md containing at least:

### Project Mission

Explain that RepoPilot is a long-term AI codebase intelligence and issue-resolution system.

### Current Stage

Stage 0 only.

### Architecture Rules

* frontend lives in apps/web
* backend lives in apps/api
* routes should remain thin
* do not implement future-stage modules early
* avoid unnecessary abstractions
* dependencies must have a concrete reason
* secrets must never be committed
* preserve clear module responsibilities

### Coding Rules

* Python code should use type hints
* TypeScript must not use `any` without explicit justification
* keep functions/modules focused
* do not perform unrelated refactors

### Testing

Document exact commands Codex should run after changes.

### Current Forbidden Scope

Explicitly forbid implementing:

* repository ingestion
* parsing
* chunking
* embeddings
* pgvector
* retrieval
* RAG
* LLM integration
* agent
* MCP
* GitHub integration
* Redis
* background jobs

---

## README

Create a minimal README containing:

* what RepoPilot is
* current development stage
* repository structure
* prerequisites
* how to install frontend dependencies
* how to install backend dependencies
* how to start backend
* how to start frontend
* how to run tests

Do not write marketing claims about functionality that does not exist yet.

Clearly distinguish:

Current functionality

from

Planned functionality.

---

## Tests

Backend must include a pytest API test verifying:

GET /api/health

returns:

HTTP 200

and the expected JSON fields.

Run the relevant backend tests.

Also verify the frontend:

* installs successfully
* TypeScript compiles
* production build succeeds

---

## Constraints

Do NOT:

* add PostgreSQL yet
* add Docker yet
* add pgvector
* add SQLAlchemy
* add Alembic
* add LLM APIs
* add RAG
* add repository import
* add Agent functionality
* add MCP
* add authentication
* add Redis
* add background jobs
* add state-management libraries
* add UI libraries
* add LangChain
* add LlamaIndex
* create speculative abstractions for future features

Do not modify or implement anything outside the defined scope.

---

## Acceptance Criteria

The task is complete only if:

1. React development app starts successfully.
2. FastAPI development server starts successfully.
3. GET /api/health returns HTTP 200.
4. Frontend successfully calls the backend.
5. UI visibly reports backend connection status.
6. Backend health test passes.
7. Frontend TypeScript validation/build passes.
8. AGENTS.md exists and documents current architecture constraints.
9. README contains accurate local development instructions.
10. No future RepoPilot functionality has been implemented.

---

## After Completion

Do not immediately make further changes.

Provide a completion report containing:

### Files Changed

List created and modified files.

### Architecture

Explain the resulting architecture and request flow.

### Dependencies

List dependencies added and explain why each one exists.

### Validation

List every command executed and its result.

### Remaining Issues

List any known problems or limitations.

### Risks

Identify anything that may cause future maintenance problems.

### Scope Check

Explicitly confirm whether any functionality outside Stage 0 Task 1 was introduced.

If Git operations are allowed in the current environment, create one meaningful commit:

feat: initialize RepoPilot application foundation
