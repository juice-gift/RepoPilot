# RepoPilot V2 Execution Plan

## Goal and boundary

Implement the authorized [V2 goal](../goals/v2-code-intelligence.md): deterministic snapshot-based symbols, definitions, imports, conservative references, independent navigation, and structural evaluation. Preserve V1 retrieval and stop before V3.

## Milestones

| Milestone | Outcome | Status |
| --- | --- | --- |
| M0 | Inspect source of truth and validate V1 baseline | Complete |
| M1 | Python AST and JS/TS syntax analyzers with explicit failure behavior | Complete |
| M2 | Versioned snapshot structural schema, migration and symbol persistence | Complete |
| M3 | Static imports and conservative references | Complete |
| M4 | Typed structural navigation APIs | Complete |
| M5 | Frozen structural golden dataset and measured evaluation | Complete |
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

Final validation and acceptance audit. No V2 implementation existed at initial HEAD 6f7f3d0.

## Dependencies / evaluation / blockers

Dependencies: tree-sitter 0.25.2, tree-sitter-javascript 0.25.0, tree-sitter-typescript 0.23.2; required for syntax-based JS/TS extraction. M1: 10 analyzer tests passed; focused Ruff passed. M2: 11 focused/live tests passed, 0004 → 0005 migration applied, alembic check clean. Symbol ID stability, persisted-content rebuild, isolation, failure atomicity and cascading cleanup verified. M3: 27 focused tests passed, including two live persistence tests; cross-snapshot foreign-key rejection, cross-file Python/TS references, all resolution statuses and stable reference IDs verified. M4: 16 API/live tests passed; exact/qualified/normalized lookup, definition source, references, imports/importers, pagination, missing resources, invalid requests and cross-snapshot symbol rejection verified. Frozen structural evaluation: 16/16 definitions, 5/5 import relations, 8/8 resolved references, all 21 occurrence statuses correct; seven symbol queries Hit@1/3/5 and MRR@1/3/5 = 1.0. Independent V1 vector/hybrid reports reproduce baseline metrics. Full suite before final fixes: 121 passed. No blockers identified.

- Real RepoPilot App.tsx exposed a native Windows access violation with tree-sitter 0.26.0. Retaining source/tree lifetimes alone did not fix it. The same file parsed repeatedly with 0.25.2; dependency constrained below 0.26 and subprocess regression coverage added. No technology change.
- Disposable-database test passed empty → V1 → V2, V2 → V1 → V2 and alembic check while preserving a V1 sentinel.

- Final review added explicit UTF-8 byte-column checks and rejected duplicate imported JS bindings instead of selecting an exported candidate. Final analyzer version is structural-v2; prior development indexes rebuild from persisted content. Failed rebuild preserves the previous index; concurrent requests serialize on the snapshot lock.
