# RepoPilot V4 — Issue Resolution Agent

**Document Status:** Approved — authorized 2026-10-21 

**Version:** V4 

**Baseline:** `d1ca7678fa482c7accea8b55afad94394413316c` 

**Target Branch:** `codex/v4-issue-resolution-agent`

## 1. Version Goal

Build the first bounded, sandboxed Issue Resolution Agent on top of RepoPilot V1–V3.

Deliver the following capability:

Issue → Investigation → Plan → Patch → Sandboxed Tests → Observation → Repair → Verification → Patch + Evidence.

The product must modify only a dedicated temporary workspace, never the original repository or RepoPilot itself.

V4 must be a real, testable code-repair workflow rather than a scripted demonstration that outputs prewritten patches.

## 2. Preflight

Before implementation:

1. Read `AGENTS.md`, `docs/PROJECT.md`, V3 Goal, V3 Plan, V3 Completion Report and relevant code.

2. Verify HEAD, branch, local working tree, latest V3 commits and documentation.

3. Run the existing backend, database, migration, lint and frontend checks.

4. Confirm V1 retrieval, V2 structural navigation and V3 tools/runner are operational.

5. Verify Docker Linux-container availability, runtime restrictions and local environment compatibility.

6. Record any verified conflicts, blockers or unexpected changes.

If a major architecture conflict or security blocker exists, stop and report it.

After successful preflight, create the authorized V4 Goal under `docs/goals/` and maintain `docs/tasks/v4-plan.md`.

## 3. Scope

### Workspace

- Create a private, per-run, independently owned workspace outside the RepoPilot source tree.

- Materialize the selected immutable Snapshot using saved and verified source data.

- Maintain snapshot identity, workspace identity and modification revision.

- Enforce limits on copied files, paths and bytes.

- Reject unsafe paths, symlink escapes and unapproved files.

- Handle workspace cleanup on success, failure, timeout and cancellation.

- Make current modified source readable during the Agent Run.

- Treat unchanged V1/V2 indexes as baseline-only evidence after modifications.

- Do not claim a V1 Snapshot alone represents an entirely executable repository.

### Patch

- Implement a bounded `apply_patch` capability.

- Validate every affected path and permitted operation.

- Prevent unauthorized changes to tests, configuration, secrets and files outside the workspace.

- Validate the expected base revision before applying a patch.

- Ensure failed patch application does not leave partial changes.

- Derive the returned Diff from actual workspace changes.

- Maintain change provenance across repair attempts.

- Do not add another overlapping editing interface unless justified by a demonstrated need.

### Sandbox

- Implement a local Docker-backed execution runtime.

- Use a trusted, reproducible Linux test image and controlled dependencies.

- Restrict source and validation mounts to the specific run.

- Mount execution inputs read-only.

- Run as an unprivileged user with network disabled, restricted capabilities, no privilege escalation, resource limits and execution timeout.

- Never mount the Docker socket or RepoPilot project directory into test containers.

- Never pass model/database/API credentials to the test process.

- Prevent model-generated commands, images or security options.

- Implement forceful timeout cleanup.

- Reject execution if mandatory isolation cannot be established.

- Do not claim Docker provides an absolute security boundary against malicious code.

### Test Execution

- Implement backend-controlled, allowlisted Test Profiles.

- Initially support a controlled Python + pytest workflow.

- Do not execute model-provided shell command strings.

- Support baseline bug reproduction and post-patch verification.

- Capture exit code, bounded stdout/stderr, elapsed time, timeout and infrastructure failures.

- Bind results to the exact tested workspace revision.

- Protect independent Golden validation tests from modification.

- Never interpret successful execution alone as proof of correct repair.

### Resolution Agent

- Reuse the existing provider/tool-calling boundary and the V3 loop mechanics.

- Make only the minimum generalization needed to support write and test tools.

- Preserve `/api/agent/investigate` and its current behavior.

- Add an explicit `submit_plan` capability.

- Require a validated plan before code modification.

- Add bounded Patch and Test tools with server-controlled permissions.

- Support iterative repair based on actual test observations.

- Enforce model-turn, patch-attempt, test-execution, output and wall-time limits.

- Preserve structured trace information without exposing hidden model reasoning.

- Differentiate completed execution, verified repair, incomplete repair and insufficient evidence.

- Support safe refusal when the issue cannot be resolved reliably.

- Keep read-only tools clearly scoped to the current workspace or baseline snapshot.

### API and UI

- Add a separate typed `POST /api/agent/resolve` endpoint.

- Return Plan, Patch, changed files, Test Results, Trace, Stop Reason and Diagnostics.

- Integrate a minimal Resolution Workflow into the existing React application.

- Show original versus modified code and actual verification status.

- Keep the existing investigation workflow available.

- Do not introduce a new UI framework, global state manager or complex task dashboard.

## 4. Out of Scope

Do not implement:

- GitHub Issue import or synchronization

- GitHub PR creation, push or remote commit

- MCP integration

- Full V6 Agent Evaluation platform

- Multi-Agent orchestration

- Arbitrary shell execution

- Unrestricted third-party dependency installation

- Arbitrary external repositories without approved execution profiles

- Production authentication and multi-tenancy

- Redis, background queue or worker infrastructure

- Production deployment architecture

- Kubernetes

- Unnecessary V1/V2 indexing redesign

- Speculative incremental indexing infrastructure

## 5. Expected Architecture

Preserve React → FastAPI → Existing Agent/Tool Boundary.

Introduce concrete V4 responsibilities only as needed:

- Workspace Manager

- Patch Engine

- Sandbox/Test Executor

- Resolution Runner

- Typed Resolution Results

- Golden Issue Fixtures

Do not force Patch or Test outputs into V3 source-evidence structures when they require different contracts.

Keep the model separate from permission enforcement. Tool argument validation, workspace ownership, patch authorization, sandbox restrictions and execution limits must be enforced by application code.

Use existing dependencies where practical. New dependencies must have a documented purpose.

## 6. Milestones

| Milestone | Deliverable |

|---|---|

| M0 | Preflight, approved V4 Goal, execution plan |

| M1 | Workspace lifecycle, executable Golden fixtures |

| M2 | Safe Patch Engine, workspace-aware reads, Diff |

| M3 | Docker Sandbox, Test Profiles, real isolation tests |

| M4 | Resolution Loop, structured Plan, bounded repair |

| M5 | FastAPI endpoint, React resolution UI |

| M6 | Frozen repair evaluation, regressions, final review |

For every milestone:

Implement → Test → Self-review → Fix → Verify → Commit → Update Plan.

Normal implementation decisions remain autonomous. Security-sensitive architectural changes require escalation.

## 7. Golden Repository and Evaluation

Create a dedicated, versioned Python Golden Issue Repository.

Freeze at least three meaningful cases before model evaluation:

1. A reproducible single-file logic bug.

2. A cross-file bug requiring correct handling of preconditions.

3. An ambiguous issue where unsupported modification should be avoided.

Positive cases must include failing baseline tests and independent expected-behavior verification. The negative case must define an explicit safe decision criterion.

Do not allow the Agent to alter evaluation ground truth.

Keep deterministic orchestration testing separate from actual external-model repair results.

Record actual repair successes, failures, unsafe decisions, patch problems and model-quality limitations. Do not infer generalized success rates from the small corpus.

## 8. Required Tests

### Unit

- Workspace creation, identity and cleanup

- Path traversal, symlink and forbidden-file rejection

- Patch validation, rollback and revision mismatch

- Current-workspace file reads

- Test Profile argument validation

- Resolution state transitions

- Model, patch and execution budget enforcement

### Integration

- Immutable Snapshot → Workspace

- Workspace → Patch → Actual Diff

- Workspace → Docker → Test Result

- Failure Observation → Repair → Retest

- Original repository and Snapshot remain unchanged

- Sandbox unavailable → Safe failure

- Independent tests remain protected

### Security

- No host source modification

- No host-shell fallback

- No network access from test container

- No credential injection

- No arbitrary command/image selection

- Enforced resource and process limits

- Timeout terminates execution

- Cleanup after failures and timeouts

- Prompt-injection instructions cannot bypass tool permissions

### Regression

- Full existing backend tests

- Live PostgreSQL integration tests

- Existing Alembic validation

- Ruff

- React production build

- V1 retrieval regression

- V2 structural regression

- V3 investigation regression

### External Model

Complete real Qwen Issue Resolution validation using the existing configured provider where credentials are available.

A deterministic or Fake Provider result cannot be presented as actual autonomous model repair success.

## 9. Acceptance Criteria

V4 is complete only if:

- The Agent can investigate an Issue, plan a change, apply a real Patch and run real sandboxed tests.

- The system can observe test failures and attempt bounded repairs.

- Successful repair cases are verified by independent tests.

- Ambiguous cases can terminate without unsafe modifications.

- All filesystem and execution isolation requirements are enforced and tested.

- The original repository and persisted Snapshot remain unchanged.

- Trace, Diff, Test Results and status accurately reflect actual execution.

- Existing V1–V3 functionality and evaluations remain intact.

- At least one actual external-model end-to-end repair succeeds under the defined Golden acceptance conditions.

- All mandatory checks actually pass.

- Documentation matches the implementation.

- No V5, V6 or V7 capabilities have been introduced.

If any mandatory verification cannot be run, mark it explicitly as unverified and do not claim full V4 completion.

## 10. Relevant Existing Files

Start by inspecting:

- `apps/api/src/repopilot/agent/runner.py`

- `apps/api/src/repopilot/agent/tools.py`

- `apps/api/src/repopilot/agent/models.py`

- `apps/api/src/repopilot/rag/tool_calling.py`

- `apps/api/src/repopilot/rag/generation.py`

- `apps/api/src/repopilot/api/routes/agent.py`

- `apps/api/src/repopilot/ingestion/scanner.py`

- `apps/api/src/repopilot/ingestion/service.py`

- `apps/api/src/repopilot/db/models.py`

- `apps/api/src/repopilot/config.py`

- `apps/web/src/AgentResult.tsx`

- Existing V3 tests and evaluation fixtures

Select new module locations based on real responsibilities; do not create speculative layers.

## 11. Git Boundary

Start from the verified V3 baseline.

Create `codex/v4-issue-resolution-agent` and commit meaningful milestones separately.

Do not rewrite V1–V3 history or modify unrelated code.

Do not push or modify the original target repositories through the product Agent.

Maintain `docs/tasks/v4-plan.md` throughout implementation.

At final acceptance, deliver:

- Files Changed

- Architecture and Data Flow

- Dependencies

- Sandbox Security Evidence

- Patch/Test Results

- Frozen Evaluation Results

- V1–V3 Regression Results

- Git Commits

- Remaining Limitations and Risks

- Scope Audit

Stop at the V4 / V5 Version Boundary.

**Authorization:** The Project Owner explicitly authorized V4 engineering execution in the objective attachment on 2026-10-21. This authorization supersedes draft approval wording and historical V3/V4 boundary notices. Stop at V4/V5.
