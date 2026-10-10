# RepoPilot V2 Execution Plan

## Goal and boundary

Deliver the authorized [V2 goal](../goals/v2-code-intelligence.md): snapshot-based deterministic symbols, definitions, imports, conservative references, independent navigation and measured structural evaluation. Preserve V1 and stop before V3.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| M0 | Inspect source of truth and validate V1 baseline | Complete |
| M1 | Python AST and JS/TS syntax analyzers | Complete |
| M2 | Versioned structural schema, migration and symbol persistence | Complete |
| M3 | Static imports and conservative references | Complete |
| M4 | Typed structural navigation APIs | Complete |
| M5 | Frozen golden dataset and structural/V1 evaluation | Complete |
| Final | Live migration, regression, build, acceptance and scope audit | Complete |

## Current state

V2 complete. Stop at the V2 / V3 boundary. No required work or blockers remain.
The [completion report](../evaluation/v2-code-intelligence-results.md) records files,
architecture, commits, commands, all acceptance items, limitations and risks.
Initial HEAD was 6f7f3d0; no V2 implementation existed at inspection.

## Important decisions

- Analyze persisted SnapshotFile.content; never execute repository code. Parser nodes stay inside analyzer modules.
- Python uses standard-library ast; JS/JSX and TS/TSX use real Tree-sitter syntax. Do not rewrite V1 chunking.
- Definition is CodeSymbol source location; files reuse SnapshotFile, with no duplicate directory or definition tables.
- Structural navigation remains independent of embeddings, LLMs and V1 ranking. No fuzzy search or fusion weights.
- Lexical bindings, shadowing, duplicate definitions and supported imports resolve conservatively with explicit reasons.
- The algorithm version is structural-v2. Repeat indexing keeps IDs; version changes rebuild saved content. Parse failure preserves the old index; snapshot row locks serialize concurrent calls.
- Composite database foreign keys prevent cross-snapshot relations and cross-version reference targets.
- Owner requested restoring the byte-equivalent uncommitted PROJECT.md relocation to docs/PROJECT.md; done before content changes.

## Dependencies and observed failure

Added tree-sitter 0.25.2, tree-sitter-javascript 0.25.0 and tree-sitter-typescript
0.23.2 to replace insufficient regex parsing for V2 JS/TS structure extraction.
Tree-sitter 0.26.0 crashed natively on Windows with the actual App.tsx; retaining
source/tree lifetimes did not fix it. 0.25.2 parsed that file repeatedly. The
supported dependency range excludes 0.26, with subprocess regression coverage.

## Validation and evaluation

- V1 baseline: ordinary 66 passed / 8 skipped; live 74 passed; migration 0004; Ruff/build passed.
- Final ordinary suite: 112 passed / 14 live database tests skipped.
- Final live database suite: 126 passed. Includes ID stability, persisted-content rebuild, failure preservation, snapshot isolation, cross-file references/imports, reverse navigation, cascading cleanup, FK rejection, concurrent idempotency and API contracts.
- Ruff passed. Alembic current is 0005_structural_index (head); alembic check found no pending operations.
- Disposable clean database replay passed empty → V1 → V2 and V2 → V1 → V2, preserving a V1 sentinel.
- Frontend TypeScript/Vite production build passed. One existing Starlette/AnyIO deprecation warning remains.
- Frozen structural corpus committed before measurement: seven symbol queries Hit@1/3/5 and MRR@1/3/5 1.0; 16/16 definitions; 5/5 import relations; 8/8 resolved reference targets; all 21 occurrence/status labels correct (8 resolved, 12 unresolved, 1 ambiguous).
- Frozen V1 rerun: vector Hit@1 0.7500, Hit@3 0.8750, Hit@5 1.0000, MRR@5 0.8375; hybrid all reported metrics 1.0000.
- Real snapshot observation: 123 files, 513 symbols, 11,012 references; 1,171 resolved, 9,840 unresolved, 1 ambiguous. No labeled ground truth: these counts do not measure accuracy.
- Final diff/security/scope audit: V1 retriever/chunker/frontend source and historical dataset unchanged; no tracked secret; no V3 or later implementation.
