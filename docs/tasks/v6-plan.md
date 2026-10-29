# V6 execution plan

Authorized scope: [goal](../goals/v6-evaluation.md). Baseline: dd1cfb5,
verified origin/main after read-only fetch and clean fast-forward. Branch:
`codex/v6-evaluation`. No remote writes authorized. Stop before V7.

| Milestone | State | Work |
| --- | --- | --- |
| M0 | In progress | Inventory V1 retrieval, V2 structure, V3 investigation, V4 repair; baseline checks |
| M1 | Pending | Typed versioned manifest linking unchanged frozen datasets; small RAG checks |
| M2 | Pending | Independent grading, applicability/denominators, missing measurements |
| M3 | Pending | CLI adapters, actual pipelines, per-case errors and owned cleanup |
| M4 | Pending | Scripted DB/Docker and bounded live Qwen pass; failure evidence |
| M5 | Pending | JSON/Markdown and guarded comparison |
| M6 | Pending | Full regressions, security review, completion evidence |

Inventory: evaluation/{runner,structural,agent,resolution}.py already implement
actual pipelines. V1 metrics must be reused. V2/V3 frozen manifests already verify
normalized content; V4 pins its manifest and protected tests. V3 grounding reviews
are exact-answer hashes. Existing providers do not expose usage consistently:
V6 will mark tokens/cost unavailable. Historical failures remain evidence.
Old V1–V3 entry points persist fixture snapshots; the unified harness will give
these adapters fresh evaluation-owned source paths and delete only those rows.
No new service, API, schema, dependency, judge model or product-agent capability.

Preflight actually executed: uv run pytest -q: 267 passed/63 opt-in skips;
npm run build: pass. Docker Linux and healthy Compose DB, immutable prepared image
71aebb88109cbb7c2eb535ef4321a4b9d23b886c0c14625bafaeb9e78b5fea5f available.
Database/sandbox full suite, Ruff and migrations running. Read goal/plan/report
for V4/V5 and inspected provider, evaluation, source, test and Git contracts.
