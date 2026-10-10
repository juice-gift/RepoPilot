# RepoPilot V2 Completion Report

Validated on 2026-10-10. V2 is complete; stop at the V2 / V3 boundary.
The authorized scope is [the V2 goal](../goals/v2-code-intelligence.md).

## Implementation and important files

- `apps/api/src/repopilot/intelligence/analysis.py`: typed parser-independent facts and index version.
- `python_analysis.py` and `javascript_analysis.py` in that directory: AST/syntax extraction, named symbols, lexical bindings, static imports and reference occurrences.
- `resolution.py`: conservative snapshot-local module and lexical definition resolution with explicit reasons.
- `service.py`: persisted-source indexing, snapshot locking, transactional replacement and same-version ID reuse.
- `navigation.py` and `apps/api/src/repopilot/api/routes/structure.py`: independent SQL navigation and typed HTTP contracts.
- `apps/api/src/repopilot/db/models.py` and migration `0005_structural_index_add_snapshot_structural_index.py`: structural persistence and integrity.
- `apps/api/src/repopilot/evaluation/structural.py`, `evaluation/structural_dataset.json`, `structural_manifest.json`, and `structural_golden/`: reproducible evaluation over human-labeled facts.
- `test_structural_analysis.py`, `test_structural_resolution.py`, `test_structural_integration.py`, `test_structure_api.py`, `test_structural_evaluation.py`, `test_structural_migration.py`: structural, failure, concurrency, migration and API regressions. The existing database-head assertion now expects V2's migration.
- README, AGENTS current stage, PROJECT current state, and `docs/tasks/v2-plan.md`: current behavior and version boundary.

The owner requested restoring the byte-equivalent uncommitted PROJECT relocation
to `docs/PROJECT.md`; the restore preserved its content before V2 status updates.
Historical V1 goal, plan, golden repository and dataset remain intact.

## Architecture and database

```text
RepositorySnapshot → SnapshotFile.content
→ Python ast / JavaScript, JSX, TypeScript, TSX syntax tree
→ typed Symbol, Import, Reference and transient lexical binding facts
→ conservative resolver
→ PostgreSQL CodeSymbol / ImportRelation / CodeReference
→ snapshot-scoped navigation → typed read-only HTTP responses
```

`POST .../structure/index` is the explicit index-building operation. Every other
structural endpoint queries saved data. Definitions use the indexed line range
and persisted file content. Complete syntax trees and transient binding scopes
are not stored. File navigation reuses SnapshotFile rather than a duplicate tree.

Migration `0005_structural_index` adds three structural tables, a snapshot version
marker and the composite uniqueness needed for same-snapshot foreign keys.
Reference targets also share their symbol's index version. Check constraints
require a target exactly when status is resolved. Snapshot deletion cascades;
schema evolution uses Alembic exclusively.

The algorithm version is `structural-v2`. Same-version calls keep symbol and
reference IDs; a version change rebuilds the snapshot's active structural records
from saved source. Rebuilds can change IDs. Clients should keep snapshot/version
context with any saved symbol ID. A snapshot row lock serializes simultaneous
index requests. Parsing finishes before replacement, and a savepoint protects
replacement writes. Failure leaves the previous index intact.

V1 semantic retrieval, ranking, embeddings, context, generation, citations and
frontend implementation were not rewritten. Structural navigation remains
independent; no fusion weights or fuzzy ranking were introduced.

## Dependencies

| Dependency | Locked version | Concrete purpose |
| --- | --- | --- |
| tree-sitter | 0.25.2 | Real JS family syntax parsing and source locations |
| tree-sitter-javascript | 0.25.0 | JavaScript / JSX grammar |
| tree-sitter-typescript | 0.23.2 | Separate TypeScript / TSX grammars |

Tree-sitter 0.26.0 produced a Windows native access violation on the actual
`apps/web/src/App.tsx`. Keeping the tree and source alive did not fix it.
The same file parsed repeatedly with 0.25.2. The dependency range stays below
0.26, and a subprocess regression test makes a future native failure observable
without terminating the pytest runner. Python keeps the working standard-library
AST path. No AI framework, graph database, worker, or other dependency was added.

## Evaluation

The structural golden expectations were committed before evaluation (`d7b758a`).
Normalized source and dataset hashes guard the frozen inputs across LF/CRLF
checkouts. The six code files plus a README are small and manually inspectable.
The runner exercises persisted PostgreSQL navigation, not an in-memory parser-only
substitute. [Full structural output](v2-structural-report.json) records every query
and discrepancy list.

| Capability | Actual result |
| --- | --- |
| Symbol queries | 7; Hit@1/3/5 = 1.0000, MRR@1/3/5 = 1.0000 |
| Definition identity and inclusive range | 16 expected, 16 returned, 16 correct; precision/recall 1.0000 |
| Static import occurrences and local targets | 5 expected, 5 returned, 5 correct; precision/recall 1.0000 |
| Resolved reference target precision/recall | 8 expected, 8 returned, 8 correct; 1.0000 / 1.0000 |
| All reference occurrence/status labels | 21/21 correct; 8 resolved, 12 unresolved, 1 ambiguous |
| Importer reverse navigation | No missing reverse relation |

Reference evaluation checks source file, reference name, line, status and target
definition identity. Byte-column accuracy has separate Python/TypeScript Unicode
tests. Duplicate output occurrences are penalized by multiset metrics.
Perfect results apply only to this explicitly labeled baseline corpus.

The unchanged frozen V1 corpus still has 8 queries, 19 chunks and 512-dimensional
deterministic token-hash embeddings. These are reproducible pipeline regressions,
not external embedding-model quality measurements.

| V1 strategy | Hit/Recall@1 | Hit/Recall@3 | Hit/Recall@5 | MRR@5 |
| --- | --- | --- | --- | --- |
| Exact vector | 0.7500 | 0.8750 | 1.0000 | 0.8375 |
| Vector + existing lexical rerank | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

See [vector regression output](v2-v1-vector-regression.json) and
[hybrid regression output](v2-v1-hybrid-regression.json). They reproduce the
recorded V1 metrics without changing its ground truth or ranking.

An additional [RepoPilot snapshot observation](v2-repository-observation.json)
indexed 123 accepted files, 513 symbols, 11,012 references and 723 import
occurrences. References: 1,171 resolved, 9,840 unresolved, 1 ambiguous; imports:
355 resolved, 368 unresolved. The persisted snapshot hash is in the report. This
snapshot includes tests, fixtures and documents at observation time and has no
manually labeled ground truth: these counts are not precision/recall measurements.

## Validation actually executed

| Command / check | Result |
| --- | --- |
| Baseline `uv run pytest` | 66 passed, 8 database tests skipped |
| Baseline `RUN_DATABASE_TESTS=1 uv run pytest` | 74 passed |
| Final `uv run pytest` | 112 passed, 14 database tests skipped |
| Final `RUN_DATABASE_TESTS=1 uv run pytest` | 126 passed |
| `uv run ruff check src tests migrations` | Passed |
| `uv run alembic upgrade head` on development DB | V1 0004 → V2 0005 applied |
| `uv run alembic current` | 0005_structural_index (head) |
| `uv run alembic check` | No new upgrade operations |
| Disposable DB migration replay in pytest | Empty → V1 → V2, downgrade to V1, re-upgrade to V2, schema checks; V1 sentinel preserved |
| `npm run build` in apps/web | TypeScript and Vite production build passed |
| `PYTHONPATH=src uv run python -m repopilot.evaluation.structural` | Report saved; metrics above |
| `PYTHONPATH=src uv run python -m repopilot.evaluation.runner --strategy vector` | Frozen V1 regression report saved |
| Same runner with `--strategy hybrid` | Frozen V1 regression report saved |
| FastAPI TestClient lifespan / OpenAPI / real structural routes | Passed in API and live suites |
| Actual RepoPilot persisted structural indexing | Passed after native dependency correction |

PowerShell environment-variable forms were used on this Windows machine.
There is one pre-existing Starlette/AnyIO deprecation warning, not a failing check.
External Qwen/OpenAI model calls were not rerun in V2; V2 does not alter those
adapters. Provider, generation, context and citation regressions passed with
test doubles/deterministic providers and the live database.

## Acceptance audit

| Goal items | Evidence |
| --- | --- |
| A1–A3: syntax analysis and honest failure | Both analyzer modules; Python/JS/JSX/TS/TSX tests, source ranges, real TSX subprocess check; invalid syntax raises AnalysisError without facts |
| B4–B7: index, rebuild, idempotency and isolation | Structural migration/service; live persisted-content, stable-ID, version-rebuild, failed-rebuild, concurrent-request and cross-snapshot FK tests |
| C8–C11: symbols and definitions | Independent symbols query, per-file filter, exact/qualified/normalized lookup and persisted definition source; live API and full golden definition comparison |
| D12–D15: imports in both directions | Static Python and ESM extraction; relative/submodule/source-root resolution; import and importer SQL, live API and golden reverse checks |
| E16–E18: conservative references | Binding resolver and explicit status/reason/nullable target; shadowing, wildcard, generic, duplicate, reassignment, lexical and cross-file tests; labeled unresolved/ambiguous results |
| F19–F21: independent structural retrieval | Navigation imports no embedding/generation provider; no V1 ranking changes; duplicate results remain separate |
| G22–G25: frozen evaluation and V1 regression | Hand-labeled dataset and source manifest committed before measurement; structural and both V1 JSON reports; frozen-input and live evaluation tests |
| H26–H30: engineering gates | Final 126 live tests, 112 isolated tests, Ruff, Alembic head/check/replay, frontend production build |
| H31–H33: documentation, dependency and diff scope | Updated current-stage/setup/API/limitation documents; only three parser dependencies; V1 retriever, chunker and frontend source unchanged |
| I34–I39: version boundary | Final source/dependency diff contains deterministic indexing/navigation only; no agent loop/tools, MCP, GitHub, code modification or test-execution agent |

Source code and tests were reviewed for unused abstractions, duplicate persistence,
parser-node leakage, untrusted repository execution, scope drift and secret files.
Repository source remains data; no parser invokes eval, exec or repository tools.
The only new subprocess execution is pytest validation of our application/parser
and Alembic against a uniquely named disposable test database.

## Git milestones

- `21ef924` docs: establish authorized V2 code intelligence plan
- `56028b4` feat: add deterministic language analysis foundation
- `24d1974` feat: persist snapshot-scoped structural symbol index
- `04a15d6` feat: index static imports and conservative symbol references
- `a8a5795` feat: expose typed snapshot structural navigation APIs
- `d7b758a` test: freeze manually verified V2 structural golden dataset
- `6508135` fix: stabilize Windows syntax analysis and conservative scope handling
- `1ad8503` fix: reject ambiguous exports and verify structural index rebuilds
- `5431070` test: evaluate structural navigation and preserve V1 regressions

Final documentation is committed separately as
`docs: complete V2 validation and record version boundary`;
no unrelated history is rewritten.

## Remaining limitations and risks

- This is static navigation, not runtime/type inference. Parameters, local
  variables and object properties are not repository symbols. Their uses often
  remain unresolved; dynamic member dispatch, framework magic and monkey patching
  have no reliable target in this baseline.
- Imports cover conventional Python roots and relative ESM modules. External
  packages, complex workspace/tsconfig aliases, namespace package layouts,
  export-list/re-export chains and runtime loading may remain unresolved.
  Multiple possible local files or definitions are returned as ambiguous.
- Rebinding and incomplete semantics deliberately reduce recall. Small golden
  precision results must not be generalized to arbitrary programs. Real-world
  corpus observation shows the unresolved volume explicitly.
- Parser grammar/runtime upgrades require validation, particularly on Windows.
  Native parser faults are a concrete compatibility risk; the known 0.26.0
  failure is excluded by the supported range and covered by the actual TSX test.
- Structural indexing is synchronous; syntax failure rejects the whole rebuild.
  There is no partial-file recovery UI, background queue or production deployment.
- Existing IDs change on algorithm-version rebuild; clients must respect snapshot
  and index version. Future semantic changes must bump the version.

No required V2 work remains. No Agent, MCP, GitHub, Code Modification,
Test Execution Agent or complete Call Graph was introduced.
**No V3 or later-version functionality was introduced.**
