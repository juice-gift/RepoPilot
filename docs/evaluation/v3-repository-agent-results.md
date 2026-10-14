# RepoPilot V3 Completion Report

Validated on 2026-10-14 under the independently authorized
[V3 goal](../goals/v3-repository-agent.md). Engineering acceptance is complete;
stop at V3 / V4. Model answer quality remains a measured baseline with failures.

## Files changed and implementation

- `apps/api/src/repopilot/agent/models.py`: typed request, source, observation,
  trace, result, stop reasons and diagnostics.
- `agent/tools.py`: five explicit allowlisted read-only tools and full-JSON bounds.
- `agent/runner.py`: explicit bounded multi-turn/multi-call execution and source-ID
  validation. Agent state is per request; no persistent runs or background subsystem.
- `rag/tool_calling.py` and `rag/generation.py`: provider-neutral turns/calls,
  minimal `complete` extension to both existing Responses providers and a clearly
  labeled deterministic local workflow. Existing V1 `generate` behavior is intact.
- `api/routes/agent.py`, `main.py`, `config.py`, `.env.example`: thin investigate
  route, settings and safe configuration template.
- `apps/web/src/api/agent.ts`, `AgentResult.tsx`, `App.tsx`, `App.css`: explicit
  HTTP contracts, existing-workflow investigation controls, trace and source views.
- Six `test_agent_*.py` files: tools, loop, adapters, HTTP, real DB and evaluation.
- `evaluation/agent_dataset.json`, `agent_manifest.json`, `agent_golden/`, and
  `evaluation/agent.py`: frozen small cross-file investigation dataset/runner.
- V3 JSON reports/reviews in this directory retain all initial/trial outputs,
  grounding failures, exact review hashes and V1/V2 regressions.
- README, AGENTS, PROJECT, V3 goal/plan and this report reflect actual behavior.

No schema, migration, dependency lockfile, V1/V2 algorithm or historical dataset
was changed. No existing module was deleted.

## Architecture and agent data flow

```text
React selected repository + snapshot + question
→ POST /api/agent/investigate → AgentRequest
→ per-run ToolRegistry / immutable RunScope → run_investigation
→ existing generation provider.complete → SDK-independent AgentTurn / ToolCall
→ name allowlist → strict typed argument validation → saved repository tool
→ bounded Observation + backend source IDs → TraceStep
→ replay call/output pairs → next model turn
→ final text + source-ID validation → AgentResult → React result/trace/sources
```

Both IDs are validated before a model request and on every tool execution.
The model never supplies or changes the scope. Tools use saved SnapshotFile,
the current V2 structural index, and the existing V1 retrieval index. Host paths
and working-tree changes cannot substitute for saved source. Missing indexes
produce explicit observations; the agent does not build or write them.

Instructions, the user's task, and untrusted repository observations remain
distinct. Reasoning output and intermediate model prose never enter trace or
replay. Only public final text, tool protocol and execution state are returned.
Source IDs are server generated; unsupported bracketed citations are marked and
listed. A valid citation is source identity, not a proof that a claim is true.

## Tools

| Tool | Implementation and limits |
| --- | --- |
| list_files | V2 persisted file navigation; sorted paths, 1–100 results, bounded offset |
| read_file | Saved SnapshotFile content; validated relative path; default 100, maximum 200 inclusive lines |
| search_code | PostgreSQL literal substring prefilter + saved line scan; case-sensitive, SQL wildcards escaped; maximum 20 snippets |
| search_symbol | Existing V2 exact/qualified/normalized symbol navigation; maximum 20 independent definitions, no duplicate index |
| retrieve_context | Existing V1 retrieve_evidence only; maximum 10 ranked sources with path/symbol/range/content/score/distance |

Argument objects reject unknown fields and coercion. Unknown tools and invalid
arguments return safe error observations without dispatch. Missing paths, indexes
and configuration can be recovered by a later model turn. Unexpected database/
embedding/tool infrastructure errors stop with `tool_failure`; provider errors
stop with `provider_failure`. Raw exceptions/credentials are not returned.

Defaults: 12 model turns (including final), five calls per turn, 4,000 argument
characters, 12,000 serialized observation characters, 60,000 accumulated input
characters including system instructions/schemas, and 12,000 model-output
characters. Existing provider token bounds also apply. Truncation preserves valid
JSON and useful source prefixes, including escaped text, with explicit flags.
No request is issued after the input budget is exceeded. A last observation can
take the retained trace/input counter above that budget and stop further calls.
`total_steps` counts tool calls; diagnostics separately count model turns.

## Provider changes and dependencies

Qwen/OpenAI reuse their existing configured models, credentials and SDK clients.
The shared Responses helper normalizes text, call IDs, names and argument strings;
SDK objects stay within that module. Calls use `store=false`, reasoning effort
`none`, bounded output, manual local history, no server response continuation,
a 30-second request timeout and zero SDK retries. The protocol was checked against
[Alibaba Cloud's official Responses documentation](https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-openai-responses).
OpenAI is contract-tested, not live-validated in V3. Qwen was live-validated.

No dependencies were added. No search service, agent framework, worker, queue,
new persistence layer or architecture replacement was introduced.

## Evaluation: actual outcomes and bad cases

Corpus/tasks were frozen before measurement in `b1fb839`. Four small saved files
cover authentication before policy, permanent/transient/negative branches, and a
documentation/implementation cap discrepancy. Every task requires multiple file
observations. Hashes guard tasks/source and exact answer/evidence reviews.

| Run | Tool calls by task | Expected evidence | Strict reviewed final grounding |
| --- | --- | --- | --- |
| Scripted PostgreSQL pipeline | 3 / 5 / 6 | 3/3 found | 3/3 prewritten answers supported; no model-quality measurement |
| Initial Qwen qwen3.7-flash | 6 / 4 / 4 | 3/3 found | 0/3 passed strict review |
| Same frozen inputs, general grounding-instruction trial | 6 / 4 / 7 | 3/3 found | 1/3 passed strict review |

The actual Qwen model, tool names, model calls, observed source, final answer and
stop reason are in [initial](v3-agent-qwen-report.json) and
[trial](v3-agent-qwen-grounding-report.json) reports. All six live investigations
finished with `completed`, including a real same-turn three-call batch. Reviews
are manual Codex source/claim comparisons, not independent human judgments.
Retrieval uses deterministic token-hash embeddings to isolate loop behavior.

Initial failures: fabricated line annotations despite correct source identity;
universal permanent-job rejection contradicting an earlier negative-attempt guard;
preferring a documentation fix without evidence of intended product behavior.
A general instruction trial asks for source-ID citations, guard-aware conclusions,
and intent-sensitive alternatives. The first answer is now source-consistent;
the other two still overgeneralize or invent production/decision assumptions.
The trial also uses extra redundant searches and parenthesized citation IDs in
one answer. Both outputs are preserved, and the safeguards are retained without
claiming a reliable accuracy improvement from one small non-repeated comparison.

The baseline records evidence discovery separately from final grounding. Raw
reports have no automatic grounding verdict; matching review hashes prevent a
verdict from silently applying to a different answer/evidence. Three controlled
tasks do not establish general repository-agent accuracy.

Frozen regressions reproduce V2 results: seven symbol queries unchanged;
16/16 definitions, 5/5 imports, 8/8 resolved reference targets, and 21/21
occurrence/status labels correct. V1 vector Hit@1/3/5 remains
0.7500/0.8750/1.0000 and MRR@5 0.8375; hybrid reported metrics remain 1.0000.
Historical ground truth, ranking and parsing algorithms were not modified.

## Validation actually executed

| Command / check | Result |
| --- | --- |
| Preflight ordinary/live pytest | 112 passed / 14 skips; 126 live passed |
| M1 focused live tools | 31 passed |
| M2 tools/loop/provider/live/V1 generation | 60 passed |
| Final ordinary `uv run pytest` | 180 passed / 16 opt-in DB skips |
| Final `RUN_DATABASE_TESTS=1 uv run pytest` | 196 passed, no skips |
| Post-review focused live V3 suite | 70 passed |
| `uv run ruff check src tests migrations` | Passed |
| `uv run alembic current` | 0005_structural_index (head) |
| `uv run alembic check` | No pending operations |
| Existing disposable migration replay test | Empty → V1 → V2; downgrade/re-upgrade and sentinel preservation passed |
| `npm run build` | TypeScript and Vite production build passed |
| Frozen scripted agent CLI | Three completed multi-tool DB runs and reports |
| Qwen agent CLI | Two runs of three real multi-step investigations; all completed |
| Structural and vector/hybrid retrieval CLIs | Baseline metrics reproduced, reports saved |
| Real FastAPI startup/TestClient/OpenAPI | Passed, including live investigate API and scope rejection |
| Browser workflow | Selected golden snapshot → investigation → two real tools → final result, expanded observation and source cards; symbol preparation checked |

PowerShell environment syntax was used on Windows. One existing AnyIO/Starlette
deprecation warning remains. The first attempted V1 regression invocation used
an unsupported `--output` option and failed; corrected stdout-saving commands
succeeded. No failed check is reported as passing without a successful rerun.

## Acceptance audit

| V3 goal items | Evidence |
| --- | --- |
| 1–7: loop, multiround and five reused tools | agent/runner.py, tools.py; scripted and Qwen DB reports |
| 8–10: scope/typed validation/safe unknown calls | immutable RunScope, strict forbidden-extra schemas; each-tool ID/scope override tests and live API 404 |
| 11–14: budgets, bounds, trace, no hidden reasoning | RunLimits, full JSON prefix regression, context/schema accounting, duplicate-call/output tests and provider normalization |
| 15–16: API and existing React product flow | thin route, explicit client guard/types, browser path and build |
| 17–23: deterministic/live/regression/build/lint/migrations | ordinary/live suites, V1/V2 frozen reports, Ruff, build, Alembic current/check/replay |
| 24–25: frozen evaluation and available Qwen validation | committed checksums/tasks, separate scripted/live reports and hashed strict verdicts |
| 26: actual-state documentation | README, PROJECT, AGENTS, goal, plan and this report |
| 27–30: later-version boundary | final source/dependency/Git audit: no writes, execution, GitHub, MCP or multiple agents |

## Git

- `82fe57a` docs: establish V3 goal after verified V2 preflight
- `51ddc2e` feat: add bounded snapshot-isolated repository agent tools
- `0695018` feat: implement explicit bounded repository investigation loop
- `9804677` feat: expose read-only investigation API and React tool trace
- `b1fb839` test: freeze multistep V3 investigation tasks and source corpus
- `96a67c7` fix: preserve useful source when bounding escaped tool output
- `0d4d03a` test: measure V3 agent baseline and preserve live grounding failures

Final actual-state documentation is committed separately as
`docs: complete V3 acceptance and record read-only agent limitations`.
Work stays on `codex/v3-repository-agent`; no unrelated history was rewritten.

## Remaining limitations, risks and scope check

- The measured final-answer failures remain. Read-only isolation prevents model
  decisions from writing/executing code, but prompt constraints cannot prove every
  sentence, precondition or recommendation. Inspect saved sources before acting.
- The dataset is tiny; Codex reviews are not independent human review. OpenAI
  live behavior and adversarial prompt-injection effectiveness were not measured.
  Tests prove data/instruction separation and tool allowlisting, not universal
  semantic resistance to untrusted text.
- Lexical search is literal and bounded, with no regex/pagination for snippets.
  Symbol navigation retains V2's static limitations. Retrieval requires an
  existing matching index. Character budgets are not exact tokenizer/cost limits.
- Runs are synchronous. No streaming step updates, run history storage, jobs or
  production auth/ownership were added. Reuse of settings/source metadata assumes
  the existing single-user local development model. SDK network timeouts are per
  request; no process cancellation or repository-code runtime exists.
- Source output may truncate/omit items. The UI distinguishes metadata-only
  symbols, saved source and truncation; observed sources are not all necessarily
  cited. Parenthesized model IDs do not become verified bracketed citations.

No required engineering acceptance work remains. No edit_file, apply_patch,
repository write, shell, arbitrary command execution, agent run_tests, sandbox,
product-agent Git commit, GitHub/PR/MCP, multi-agent, worker/queue/Redis or production
deployment functionality was introduced. Development test/Git commands are the
engineering workflow, not capabilities exposed to the product agent.
**Stop at the V3 / V4 version boundary.**
