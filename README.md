# RepoPilot

RepoPilot is a long-term AI codebase intelligence and issue-resolution system. The project is currently at **Stage 0 — Project Inception**.

## Current functionality

The current application is a minimal end-to-end development path:

```text
React UI -> HTTP GET /api/health -> FastAPI -> JSON response -> React UI
```

The browser reports whether it can connect to the backend. No database or AI functionality is implemented yet.

## Planned functionality

Later project stages may add repository ingestion, code-aware retrieval, RAG, issue analysis, agent workflows, GitHub/MCP integration, evaluation, and production engineering. These capabilities are planned only and are not part of the current application.

## Repository structure

```text
RepoPilot/
├── apps/
│   ├── api/    # FastAPI backend and backend tests
│   └── web/    # React + TypeScript frontend
├── docs/       # Project charter and scoped task specifications
├── AGENTS.md
├── README.md
└── .gitignore
```

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Node.js 22 or later
- npm

## Install dependencies

Backend:

```bash
cd apps/api
uv sync
```

Frontend:

```bash
cd apps/web
npm install
```

## Run locally

Start the backend from `apps/api`:

```bash
uv run uvicorn --app-dir src repopilot.main:app --reload
```

The API is available at `http://localhost:8000`. Its health endpoint is `http://localhost:8000/api/health`.

Start the frontend in another terminal from `apps/web`:

```bash
npm run dev
```

Open `http://localhost:5173`. The page checks the backend and displays the connection state.

## Run validation

Backend tests, from `apps/api`:

```bash
uv run pytest
```

Frontend TypeScript validation and production build, from `apps/web`:

```bash
npm run build
```
