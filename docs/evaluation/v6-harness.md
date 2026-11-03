# V6 evaluation harness

Run from `apps/api` in PowerShell after the documented database migration and
sandbox-image preparation. No new dependency or migration is required.

```powershell
$env:PYTHONPATH = 'src'
$env:RESOLUTION_SANDBOX_IMAGE = 'sha256:71aebb88109cbb7c2eb535ef4321a4b9d23b886c0c14625bafaeb9e78b5fea5f'
uv run python -m repopilot.evaluation.harness run --output ../../docs/evaluation/local-scripted.json
uv run python -m repopilot.evaluation.harness run --category retrieval --strategy vector --output ../../docs/evaluation/local-vector.json
uv run python -m repopilot.evaluation.harness run --mode live --category resolution --output ../../docs/evaluation/local-qwen.json
uv run python -m repopilot.evaluation.harness compare ../../docs/evaluation/local-scripted.json ../../docs/evaluation/local-scripted.json --output ../../docs/evaluation/local-comparison.json
```

Use your locally inspected immutable sandbox image identity. The displayed image
is this environment's actual prepared image, not a portable registry tag.
`--category` and `--case` repeat; case IDs include category prefixes, e.g.
`--case resolution/ambiguous-cap`. `--dataset` accepts only a contract matching
the pinned canonical dataset identity and frozen inputs. Unknown/empty selections
fail before execution. The legacy V1–V4 CLIs remain available unchanged by default.

Live uses the configured Qwen model/key, never falls back, and runs each selected
case once. Full live selection includes three investigations, two RAG questions,
and three Issues; explicitly select categories to bound cost. Retrieval and
structural measurements always use deterministic embeddings/static code and must
not be mistaken for external embedding quality. Provider usage/cost are null.
Nonzero exit means a failed/provider/infrastructure case; unreviewed semantic
claims remain unverified even when the CLI completes successfully.

The pinned dataset has 17 tasks: eight frozen V1 queries; one V2 structural suite
(16 definitions, five imports and 21 reference occurrences, not one code example);
three frozen V3 investigations; two manually inspectable V1-source RAG questions;
and the original three V4 issue profiles. Goldens, scripts, protected tests and
reference answers remain evaluator-side; only normal question/source/tool inputs
reach real providers. Frozen source/dataset identity includes normalized UTF-8
content hashes and exact source file sets. Existing manifest hashes are preserved.

Data flow: validate dataset → temporary copied sources → existing retrieval,
structural, investigation, RAG or resolution pipeline → independent grader →
per-case JSON plus Markdown → guarded comparison. V4 creates its own verified
workspace and actual restricted Docker tests. V1–V3 adapters ingest unique temporary
paths; finalizers delete only rows matching those owned paths, then the temporary
directories. Existing application snapshots are never rebuilt/deleted. No GitHub
client, publication, approval, network mutation or new execution mechanism is used.

Metric definitions:

- Task success: passing V4 frozen independent criteria / all selected Issue tasks.
- Verified repair: source-safe actual repair with reproduced failing baseline and
  exact final revision, profile, workspace, count and isolation/cleanup test evidence
  / all selected positive Issues. Patch application alone cannot pass.
- Safe decision: needs_owner_decision with revision zero, no patch/changed files or
  patch attempts, intact source/snapshot and cleaned workspace / decision tasks.
  This is never counted as a verified repair.
- Patch apply (task coverage): tasks with a recorded successful patch / applicable positive tasks.
  `patch_apply_attempts` separately reports recorded successful patch applications / actual
  patch attempts; zero attempts yield null and missing attempt evidence stays explicit.
  Missing attempts remain not_run; per-attempt history/attempt counts are in JSON.
- Independent test: passing exact-revision protected test evidence / positive Issues.
- Evidence discovery: tasks with all declared evidence / applicable tasks. V1 also
  reuses existing Hit@1/3/5, macro Recall and MRR (sum of query contributions / query
  count). A missing executed ranking contributes no retrieved evidence.
- Citation validity: at least one parsed reference and no invalid IDs / generated
  investigation and RAG tasks. Citation identity separately compares cited content
  and line spans with the exact frozen source. Neither proves semantic support.
- Claim support: explicit supported judgments / all generated tasks requiring
  review, with unverified coverage and reviewed-only denominator/rate shown; no review yields null quality. Unreviewed claims do not become failures
  or pass semantic quality. Repair correctness and repair prose remain separate.

All numerator/denominator/status counts are reported. `not_applicable` is excluded;
`not_run`, `unverified`, failed and provider/infrastructure cases stay visible.
An empty denominator yields null. Latency includes adapter setup/cleanup; raw V4
model duration is retained separately. Tool/model counts show measurement coverage.

To add a concrete review, create a JSON array of objects with `id`, `evidence_hash`
(SHA256 using `contracts.digest(case.evidence)`), `supported` (boolean), `reviewer`,
`provenance`, and `reason`. Then use:

```powershell
uv run python -m repopilot.evaluation.harness review run.json reviews.json --output reviewed.json
```

Human versus Codex source review must be labeled truthfully. Reviews bind exact
saved outputs/evidence, never a task ID alone. Historical V3/V4 reviews are verified
against their original output hashes, included as separate provenance and excluded
from current-run scores. This retains prior unsupported claims and quota failures.
No judge model is introduced. Historical review wording remains historical.

Comparison rejects different dataset/hash, ordered selection, scoring definition,
mode, review policy, model, sandbox/runtime and prompt/implementation fingerprints,
and incomplete runs or inconsistent aggregates. This intentionally conservative
comparison supports repeated same-configuration runs; changing a critical config
requires explicitly designing a new compatible experiment, not bypassing checks.
A single repetition does not demonstrate general accuracy or improvement.

JSON is checkpointed after each case, including safe error type diagnostics. Raw
exception messages are excluded because provider/DB failures can contain secrets.
Reports contain only the approved public frozen fixtures and explicit tool traces,
not credentials or hidden model reasoning. Do not point output at frozen inputs.
There is no RAG/investigation semantic accuracy claim until an exact-output review.

Final acceptance evidence and measured bad cases are in
[v6-evaluation-completion.md](v6-evaluation-completion.md). Dataset v2 corrects a new
v1 fee annotation; v1 execution reports retain their original dataset hashes.
`docs/tasks/v6-diagnose.py` reproduces labeled offline source review/diagnosis
without additional model calls. V1 trials and v2 final runs must not be compared.
