# RepoPilot V6 — Evaluation System

## 0. Authorization and Execution Mode

This message explicitly authorizes the complete implementation of **V6 — Evaluation System**, superseding the historical V5/V6 stop boundary for V6 engineering work only.

The authoritative repository is `juice-gift/RepoPilot`, based on the latest verified local `main` containing the merged V5 implementation.

First, persist this specification as:

`docs/goals/v6-evaluation.md`

Create an independent development branch, preferably `codex/v6-evaluation`, after checking the real Git state.

Use the existing **Autonomous Goal** workflow defined in `AGENTS.md`.

You are authorized to autonomously:

- Inspect the repository and relevant Git history.
- Create and maintain `docs/tasks/v6-plan.md`.
- Decompose V6 into meaningful milestones.
- Implement the complete approved V6 scope.
- Write tests and evaluation datasets.
- Execute tests, reproduce failures, debug and fix.
- Perform safe database and Docker validation.
- Run bounded evaluation experiments.
- Review your changes and remove unnecessary complexity.
- Create meaningful local Git commits.
- Update documentation and produce a completion report.

Do not stop between routine milestones for human approval.

Do not stop after only producing an implementation plan.

Continue through implementation, validation, self-review and completion, unless an escalation condition in `AGENTS.md` is reached.

Do not enter V7.

Do not push, merge, create remote PRs or perform GitHub repository mutations without separate authorization.

## 1. Context

RepoPilot has completed:

- V1 — Codebase RAG
- V2 — Code Intelligence
- V3 — Read-only Repository Agent
- V4 — Issue Resolution Agent
- V5 — MCP + GitHub Integration

The V5 completion report records a controlled GitHub Issue → immutable Snapshot → V4 repair → independent Docker tests → explicit human approval → Draft PR workflow.

V5's acceptance is limited to approved frozen fixtures, not arbitrary repositories or general issue-resolution reliability.

Existing evaluation capabilities include:

- V1 frozen retrieval dataset and Hit@K, Recall@K, MRR calculations.
- V2 structural Golden Dataset and navigation accuracy measurements.
- V3 scripted and real-Qwen investigation evaluation, including documented grounding failures.
- V4 frozen issue-resolution profiles, scripted/real-Qwen evaluation, actual patches and independent Docker tests.
- V5 protocol, persistence, approval, publication and regression evidence.

These capabilities are valuable but are not yet a unified, repeatable evaluation workflow.

Do not assume existing evaluations are missing. Inspect and reuse them.

## 2. Goal

Build a complete, independently executable **RepoPilot Evaluation Harness** that measures and diagnoses the quality of the existing retrieval, RAG, repository investigation and issue-resolution capabilities.

The intended workflow is:

```text
Frozen Evaluation Dataset
    ↓
Evaluation Runner
    ↓
Existing RepoPilot Components
    ├── Retrieval
    ├── RAG
    ├── Repository Agent
    └── Issue Resolution Agent
    ↓
Independent Evidence and Tests
    ↓
Deterministic Graders / Reviewed Judgments
    ↓
Metrics + Failure Classification
    ↓
Reproducible Evaluation Report
    ↓
Controlled Experiment Comparison
```

The system must distinguish:

1. Whether relevant evidence was retrieved.
2. Whether the generated answer was supported by evidence.
3. Whether the Agent investigated appropriate code.
4. Whether the Agent correctly repaired an Issue or safely declined an ambiguous task.
5. Whether independent tests verified the result.
6. Whether improvements are supported by comparable measurements.
7. How much time, model usage and tool activity the execution required.

The goal is measurable engineering evidence, not impressive-looking scores.

## 3. Architectural Boundaries

Preserve the existing:

- React + TypeScript frontend.
- FastAPI backend.
- PostgreSQL + pgvector persistence.
- V1 retrieval and RAG implementation.
- V2 structural indexing/navigation.
- V3 tool-calling Agent.
- V4 bounded repair loop and sandbox.
- V5 MCP/GitHub permission and publication boundaries.

Implement V6 primarily within the existing Python evaluation package.

Prefer a CLI-driven evaluation harness with JSON and Markdown outputs.

Do not create a new backend service, API surface, database schema or React dashboard unless a demonstrated V6 requirement cannot reasonably be met without one.

Prefer existing libraries, models, providers and test infrastructure.

Keep evaluator logic independent of the system being evaluated.

Avoid circular dependencies and hidden modifications to Agent decisions.

## 4. Required Milestones

### M0 — Preflight and Evaluation Inventory

Before implementation:

1. Read `AGENTS.md`, `docs/PROJECT.md`, the V4/V5 goals, plans and completion reports.
2. Inspect actual code, tests, evaluation modules, frozen fixtures and Git history.
3. Verify the latest local `main` and worktree state. Do not discard uncommitted changes.
4. Run relevant existing backend, database, sandbox, migration and frontend checks.
5. Identify reusable evaluation entry points, contracts and data.
6. Record current evaluation limitations and missing capabilities.
7. Create a concise V6 execution plan.

Treat historical reports as recorded evidence, not as proof that current execution has passed.

If documentation and implementation materially disagree, report the conflict and follow the project's escalation rules.

### M1 — Unified Evaluation Dataset and Ground Truth

Define explicit, typed, versioned evaluation dataset contracts.

Cover four dimensions:

**A. Retrieval**

Reuse V1's existing frozen query-to-evidence judgments.

**B. Code Intelligence / Investigation**

Reuse V2 structural and V3 investigation datasets and source judgments.

**C. RAG Grounding**

Define a small, manually inspectable set of source-grounded answer checks using existing known code and evidence.

Separate valid citation identity from actual claim support.

A citation pointing to real source code is not automatically proof that an answer is correct.

**D. Issue Resolution**

Reuse the V4 frozen profiles:

- `fee-days`
- `dispatch-preconditions`
- `ambiguous-cap`

Preserve the existing immutable source and independent tests.

Classify positive repair tasks separately from tasks whose correct outcome is `needs_owner_decision`.

Do not count an expected safe refusal as a successful code repair.

Do not manufacture additional Issue cases merely to enlarge the dataset. Add cases only if they provide legitimate, independently verifiable coverage without expanding V4's authorized execution scope.

Dataset requirements:

- Unique stable task IDs.
- Task category and expected outcome.
- Frozen source/version identity.
- Expected evidence or independent success criteria.
- Integrity checks and dataset version.
- Explicit treatment of incomplete or unsupported tasks.
- No evaluation-only answers, reference patches or protected test solutions disclosed to the evaluated Agent.

Preserve all historical Golden Datasets and their hashes.

### M2 — Independent Graders and Metrics

Implement independently testable grading and aggregation logic.

**Retrieval metrics**

Reuse or extend the existing:

- Hit@K
- Recall@K
- MRR

Do not duplicate functioning implementations.

**RAG / Investigation metrics**

Measure separately:

- Required evidence discovery.
- Citation validity.
- Citation-to-source identity.
- Available claim-support judgments.
- Unsupported citation or claim cases.

Where semantic grounding requires human review, represent the result as unreviewed until a concrete review exists.

If historical manually reviewed results are reused, verify their content hashes and label their provenance.

Do not introduce LLM-as-a-Judge merely to create an automatic quality score.

**Issue Resolution metrics**

Implement clearly defined:

- Task Success Rate.
- Verified Repair Rate for positive repair tasks.
- Correct Safe-Decision Rate for decision/negative tasks.
- Patch Apply Success Rate.
- Independent Test Pass Rate.
- Tool Calls / Model Turns.
- End-to-end Latency.
- Token Usage and estimated/recorded Cost where trustworthy data is available.

Define all denominators and applicability rules explicitly.

Distinguish:

- `passed`
- `failed`
- `not_applicable`
- `not_run`
- `unverified`
- infrastructure/provider errors

A missing test result is not a passing test.

A completed Agent loop is not necessarily a successful task.

A syntactically applied patch is not necessarily a correct repair.

Do not silently treat missing token usage as zero.

If existing provider boundaries do not expose reliable token usage, either make a minimal, backward-compatible usage propagation change or mark those values unavailable. Do not fabricate usage or cost.

### M3 — Evaluation Runner

Build an executable runner integrating the existing evaluation components.

Required capabilities:

1. Load and validate an evaluation dataset.
2. Select evaluation category, cases, and execution mode.
3. Verify required infrastructure and configuration.
4. Invoke the actual existing RepoPilot pipeline.
5. Capture structured outputs and diagnostics.
6. Invoke independent graders.
7. Preserve per-case results, including failures.
8. Produce machine-readable output.
9. Clean up evaluation-owned temporary resources.
10. Never mutate frozen source fixtures or existing repository Snapshots.

Support at least two clearly differentiated execution modes:

**Deterministic / Scripted**

For regression testing, metrics, orchestration and repeatability.

Must be explicitly labeled as not measuring real LLM reasoning quality.

**Live Model**

Use the existing configured Qwen provider and actual V3/V4 workflows.

Live evaluation must not silently fall back to scripted execution.

Reuse the existing V4 sandbox restrictions, test profiles, revision tracking and cleanup behavior.

Do not create a second Agent implementation or a second unrestricted command executor.

Use the existing evaluation routines through narrow adapters or modest refactoring where justified.

Avoid deleting/rebuilding unrelated application data.

The runner should support a documented CLI entry point. The final executable command and arguments must reflect the implementation actually created, not an assumed interface.

### M4 — Real Evaluation and Failure Diagnosis

Run the frozen evaluations using the available local infrastructure.

Required:

- V1 retrieval baseline and retained strategy.
- V2 structural regression.
- V3 scripted investigation.
- V4 scripted issue resolution with actual independent Docker tests.
- V6 unified grading/reporting over those results.

Also run bounded live Qwen evaluation when the existing configured credentials, quota and runtime are available.

Prefer one bounded full pass over the existing controlled Issue cases before considering reruns.

Do not silently trigger extensive paid model experiments or unlimited retries.

If live credentials, quota or required Docker/database infrastructure are missing, finish independent implementation work where possible, report the exact blocker and leave live quality unverified.

Classify failures using actual evidence, including:

- Retrieval failure.
- Missing or irrelevant evidence.
- Unsupported final claims.
- Incorrect root-cause conclusion.
- Incorrect task decision.
- Invalid or failed patch.
- Independent test failure.
- Agent limit exhaustion.
- Provider failure.
- Sandbox/infrastructure failure.
- Insufficient evaluation evidence.

Do not rely solely on an LLM-written explanation to determine the failure category.

Record concrete bad cases and provide traceable evidence.

Existing V3/V4 answer-grounding failures must not disappear merely because the new reporting framework is introduced.

### M5 — Experiment Comparison and Reporting

Generate structured evaluation reports.

At minimum:

- Machine-readable JSON report.
- Human-readable Markdown summary.
- Dataset name, version, hash and task count.
- Git commit under evaluation.
- Provider/model/configuration identity.
- Execution mode.
- Relevant Prompt or configuration fingerprints when safely available.
- Sandbox image identity and environment metadata where relevant.
- Per-case outcome, evidence and failure reason.
- Aggregate metrics with numerators and denominators.
- Token/cost/latency data where actually measured.
- Missing measurements and limitations.

Never include credentials, confidential repository content or hidden model reasoning.

Build a comparison mechanism allowing two compatible evaluation runs to be compared.

A comparison must check critical compatibility conditions, including dataset identity, task selection, evaluation definitions and relevant runtime configuration.

Clearly flag or refuse invalid apples-to-oranges comparisons.

For nondeterministic model evaluation, record repetitions separately. Never imply a single successful run demonstrates general reliability.

The report must make it straightforward to answer:

- What improved?
- What regressed?
- What failed?
- Why did it fail?
- What evidence supports the conclusion?
- What remains uncertain?

An actual measured improvement is not required for V6 acceptance.

A trustworthy negative result is preferable to a fabricated positive result.

### M6 — Final Validation, Documentation and Completion

Run all relevant verification:

- Backend tests.
- Evaluation unit and integration tests.
- Database-enabled tests.
- Docker sandbox tests.
- Ruff.
- Alembic current/check and migration replay where applicable.
- Frontend production build.
- Frozen V1–V5 regression checks.
- Evaluation CLI smoke tests.
- Report generation and comparison tests.
- Final security and scope review.

Only run optional live MCP/GitHub checks under their existing explicit safe configuration. V6 evaluation must not publish commits, change remote branches, create PRs or approve proposals.

Update:

- `README.md`
- `AGENTS.md` current stage.
- `docs/PROJECT.md` current state.
- `docs/tasks/v6-plan.md`
- Relevant evaluation documentation.

Create:

`docs/evaluation/v6-evaluation-completion.md`

The completion report must contain actual commands and measured results.

Retain important failures, limitations and non-executed validation.

Stop at V6/V7.

## 5. Required Test Coverage

At minimum, add regression tests for:

- Invalid, duplicate and tampered dataset entries.
- Dataset/hash incompatibility.
- Correct metrics and denominators.
- Empty or incomplete evaluation runs.
- Negative-case scoring.
- Patch success versus actual repair success.
- Missing test evidence.
- Invalid citations and unsupported evidence references.
- Infrastructure/provider failure classification.
- Unavailable token/cost reporting.
- Invalid experiment comparisons.
- Frozen fixture integrity.
- Temporary workspace/container cleanup.
- No unauthorized repository or remote GitHub mutation.
- Backward compatibility with existing V1–V5 interfaces.

Use deterministic fixtures for grading tests.

Use real PostgreSQL/Docker integration where meaningful and available.

Mocks alone cannot prove end-to-end repair evaluation.

## 6. Out of Scope

Do not implement:

- A new repository-solving Agent.
- A multi-agent judge system.
- An unrestricted repair/execution mechanism.
- Arbitrary third-party repository execution.
- A general SWE-bench infrastructure clone.
- Full SWE-bench leaderboard evaluation.
- LangChain/LlamaIndex evaluation frameworks without demonstrated need.
- A new frontend dashboard by default.
- A new microservice.
- Redis, Celery or background job queues.
- Production authentication or multi-user permissions.
- Production deployment or cloud infrastructure.
- New V7 observability infrastructure.
- Automatic model fine-tuning or Prompt optimization loops.
- Automatic GitHub commits, branch mutation, PR publication or merging by the evaluated product Agent.
- Unrelated V1–V5 refactors.

Use existing components unless a concrete engineering problem justifies a narrowly scoped change.

## 7. Acceptance Criteria

V6 is accepted only when:

1. A real, independently executable Evaluation Harness exists.
2. Existing frozen V1–V4 evaluation capabilities are reused without changing their Ground Truth.
3. Retrieval, RAG/investigation and Issue Resolution are evaluated as distinct dimensions.
4. The V4 positive and ambiguous cases receive semantically correct, separate grading.
5. Actual independent Docker test evidence is evaluated instead of only trusting Agent output.
6. Scripted and external-model measurements are never conflated.
7. Per-case and aggregate results are reproducible, inspectable and correctly labeled.
8. Failures, unavailable measurements and invalid comparisons are represented honestly.
9. JSON/Markdown reports are generated from actual runs.
10. Existing V1–V5 capabilities and safety boundaries remain intact.
11. Relevant automated tests, migrations, lint and build pass.
12. A complete V6 engineering report and meaningful Git history exist.

When configured live Qwen execution is available, demonstrate at least one actual bounded V6 live-model evaluation and preserve its evidence.

If live verification cannot run, report it explicitly as an outstanding acceptance blocker rather than marking it passed.

Do not claim general issue-resolution accuracy from a three-case frozen corpus.

Do not claim an improvement unless measured under genuinely comparable conditions.

## 8. Git and Autonomous Execution

Follow:

```text
Read Source of Truth
→ Verify Baseline
→ Create V6 Branch
→ Create Execution Plan
→ Implement Milestone
→ Run Tests
→ Diagnose and Fix
→ Self-review
→ Commit
→ Update Plan
→ Continue
→ Full Regression
→ Completion Report
→ Stop
```

Use meaningful, reviewable local commits.

Do not overwrite unrelated changes.

Do not modify existing frozen baselines merely to make tests pass.

Do not rewrite Git history.

Do not push or merge remotely without separate authorization.

Do not pause for routine choices within the approved V6 scope.

Escalate only for material architecture conflicts, required permission decisions, destructive operations, unavailable mandatory credentials/infrastructure, or unrecoverable validation blockers.

## 9. Final Response Required

When implementation is complete or genuinely blocked, report:

1. **Implemented Milestones** — completion status for M0–M6.
2. **Architecture** — actual evaluation data flow and reused components.
3. **Files Changed** — important source/test/documentation changes.
4. **Evaluation Results** — actual metrics, sample sizes and execution modes.
5. **Validation** — exact commands, passed/failed/skipped counts.
6. **Dependencies/Migrations** — changes and justification, or explicitly none.
7. **Git** — branch, commits and worktree status.
8. **Limitations** — actual known evaluation and Agent limitations.
9. **Remaining Blockers** — what could not be verified and why.
10. **Scope Audit** — confirmation that V7 and unauthorized remote mutations were not introduced.

The final verdict must clearly distinguish:

- Engineering implementation complete.
- Evaluation validated.
- Evaluation quality limitations.
- Any remaining acceptance blockers.

Do not describe V6 as fully accepted unless the required acceptance evidence exists.

**Final boundary: V6 Evaluation System complete, or explicitly blocked with evidence. Stop before V7 Production Engineering.**