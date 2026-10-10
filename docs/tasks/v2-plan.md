# RepoPilot V2 Execution Plan

## Goal and boundary

Implement the authorized [V2 goal](../goals/v2-code-intelligence.md): deterministic snapshot-based symbols, definitions, imports, conservative references, independent navigation, and structural evaluation. Preserve V1 retrieval and stop before V3.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| M0 | Inspect source of truth and validate V1 baseline | Complete |
| M1 | Python AST and JS/TS syntax analyzers with explicit failure behavior | Complete |
| M2 | Versioned snapshot structural schema, migration and symbol persistence | Complete |
| M3 | Static imports and conservative references | Pending |
| M4 | Typed structural navigation APIs | Pending |
| M5 | Frozen structural golden dataset and measured evaluation | Pending |
| Final | Live migration, regression, build, acceptance and scope audit | Pending |

## Decisions

- Read only persisted SnapshotFile content; never execute repository code.
- Python uses standard-library ast; JS/JSX and TS/TSX use minimal Tree-sitter grammar dependencies.
- Parser nodes remain inside analyzers. Extraction and resolution use plain typed records.
- Definitions are CodeSymbol source locations; no duplicate definition or directory table.
- Structural navigation remains independent of general retrieval; no ranking changes without measured need.
- Conservative resolution favors unresolved over an unsupported semantic claim.
- Existing uncommitted PROJECT.md relocation was byte-equivalent; owner requested restoring docs/PROJECT.md, completed without content edits.

## Validation and baseline

- Ordinary V1 tests: 66 passed, 8 database tests skipped.
- Ruff: passed. Frontend production build: passed.
- Live V1 suite: 74 passed; migration at 0004 head; alembic check clean. Frozen evaluation is covered by the live suite; full metric reports are also rerun at final validation.

## Current work

M3 import and reference resolution. No V2 implementation existed at initial HEAD 6f7f3d0.

## Dependencies / evaluation / blockers

Dependencies: tree-sitter 0.26.0, tree-sitter-javascript 0.25.0, tree-sitter-typescript 0.23.2; required for syntax-based JS/TS extraction. M1: 10 analyzer tests passed; focused Ruff passed. M2: 11 focused/live tests passed, 0004 → 0005 migration applied, alembic check clean. Symbol ID stability, persisted-content rebuild, isolation, failure atomicity and cascading cleanup verified. No measured V2 results yet. No blockers identified.



