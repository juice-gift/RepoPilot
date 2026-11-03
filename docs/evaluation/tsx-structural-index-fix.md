# TSX structural indexing repair — 2026-11-03

Scoped post-V6 bug fix; no V7 work. Starting branch `codex/v6-evaluation`,
HEAD `5dac7e9`, clean worktree. Read AGENTS.md, PROJECT.md, V6 goal and relevant
parser history (including the Windows native-crash fix `6508135`).

## Root cause and reproduction

Actual installed **and uv.lock-pinned** versions: tree-sitter 0.25.2,
tree-sitter-typescript 0.23.2, tree-sitter-javascript 0.25.0.
The TSX grammar rejects bare ampersands in JSX text that TypeScript accepts.
This is a parser compatibility failure, not a TypeScript syntax error.

In `apps/web/src/AgentResult.tsx`, line 19:

```tsx
      <h4>Tool calls & observations</h4>
```

Raw Tree-sitter reports exactly one ERROR: `& observations`, line 19,
columns 22–35 inclusive (UTF-8 byte columns, one-based). No MISSING nodes.
Native points are `(18, 21)` to `(18, 35)` (zero-based, exclusive end).
The persisted Snapshot source reproduces the same failure; its only difference
from the working file is CRLF versus LF.

Reproduce from `apps/api` without application normalization:

```powershell
@'
from pathlib import Path
from importlib.metadata import version
from tree_sitter import Language, Parser
import tree_sitter_typescript
print({n: version(n) for n in ('tree-sitter', 'tree-sitter-typescript', 'tree-sitter-javascript')})
source = Path('../web/src/AgentResult.tsx').read_bytes()
root = Parser(Language(tree_sitter_typescript.language_tsx())).parse(source).root_node
pending = [root]
while pending:
    node = pending.pop()
    if node.is_error or node.is_missing:
        print(node.type, node.is_missing, node.start_point, node.end_point,
              repr(source[node.start_byte:node.end_byte].decode('utf-8')))
    pending.extend(reversed(node.children))
'@ | uv run --locked python -
```

`npm exec tsc -- -b --pretty false` and `npm run build` from `apps/web`
both exit 0 before the repair; build also passes afterward. Build runs
`tsc -b && vite build`. No frontend source was changed.

## Implementation and regression coverage

Only the JS-family analysis boundary changes. On erroneous JSX/TSX trees,
recognized JSX boundaries identify text regions. A temporary parse buffer masks
ampersands in those regions with one-byte spaces. Original source, newlines,
UTF-8 byte offsets, expressions and attributes remain intact. Extraction reads
the original source. Reparse must have **zero errors**; remaining ERROR/MISSING
nodes still raise AnalysisError, now with up to five node locations.
Recovery can expose another text region; retries require at least one new mask
and terminate when no progress is possible. This is a targeted compatibility
workaround, not a general TypeScript validator or a promise to support all syntax.

Tests read the actual AgentResult.tsx and check both exported functions, ranges,
import and deterministic results. Additional JSX/TSX cases cover fragments,
entities, consecutive ampersands, UTF-8 offsets, retained bitwise-expression
references, and rejection of broken expressions/attributes/delimiters and
unrelated syntax errors. Initial mixed-entity tests exposed incomplete recovery;
the final progress-based retry passes them.

No file skipping, weakened final error guard, dependency/lock/migration changes,
index contract changes, remote writes or unrelated architecture changes.
Existing successful indexes need no version bump: text contributes no symbols.

## Actual validation

From `apps/api`:

- `uv run --locked pytest`: **310 passed, 64 skipped**. Opt-in database,
  Docker and online tests remain skipped in this ordinary invocation.
- `uv run --locked pytest tests/test_structural_analysis.py tests/test_structural_resolution.py tests/test_structural_evaluation.py tests/test_structure_api.py`:
  **59 passed, 1 database skip**.
- With `$env:RUN_DATABASE_TESTS='1'`, `uv run --locked pytest tests/test_structural_integration.py tests/test_structural_evaluation.py`:
  **7 passed**, including frozen structural evaluation and persistence.
- `uv run --locked ruff check src tests migrations`: passed.
- Changed Python files: `ruff format --check` passed.
- An exploratory `ruff check .` reports 8 existing violations in frozen
  evaluation fixtures / sandbox; those files were deliberately left unchanged.
- `npm run build` from `apps/web`: passed (39 transformed modules).

## Existing Snapshot verification and operation

Hash prefix `893fd9a98d` uniquely matched repository **28**, snapshot **1311**:
235 saved files, 1774 chunks and 1774 indexed embeddings; structural version
was initially null. All 235 persisted files parsed successfully after repair.
Invoking the actual index service against this Snapshot produced:

```json
{"snapshot_id":1311,"index_version":"structural-v2","symbol_count":1147,"import_count":1745,"reference_count":25868,"created":true}
```

Both `InvestigationResult` (lines 3–35) and `InvestigationSources` (37–57)
were found and their saved definitions read successfully. A repeated index call
returned identical counts and `created:false`. Source hash, chunk count,
indexed embedding count and embedding timestamp were checked unchanged.

**No re-Ingest or Qwen Embedding run is required.** The existing Snapshot is
already structurally indexed by this repair session. Restart any backend process
that has not loaded the updated code, then refresh the UI. Prepare symbol
navigation is safe to repeat and should return the existing index.

To verify using the running backend, issue:

```text
POST /api/repositories/28/snapshots/1311/structure/index
GET /api/repositories/28/snapshots/1311/structure/symbols?q=InvestigationResult&file_path=apps/web/src/AgentResult.tsx
GET /api/repositories/28/snapshots/1311/structure/symbols?q=InvestigationSources&file_path=apps/web/src/AgentResult.tsx
GET /api/repositories/28/snapshots/1311/structure/symbols/{returned_symbol_id}
```

The same routes were exercised through FastAPI TestClient with the real database
session: index and both lookups/definitions returned HTTP 200. This verifies the
API implementation; an already-running server/browser was not restarted or tested.
