# RepoPilot V5 — MCP + GitHub Integration

**Status:** Authorized by the project owner on 2026-10-27; local preflight complete.
M1 read-only MCP boundary and actual official-server reads verified. Controlled
fixture source, baseline and Issue bodies verify; M2 persistence is complete.
M3–M6 and V5 acceptance remain incomplete.
**Baseline:** `0308e8ab588d8d2a15ad960325e1d062f330eb45` on clean `main`.
**Branch:** `codex/v5-mcp-github`.
**Execution plan:** [V5 plan](../tasks/v5-plan.md).

## Goal and authorization

Build on completed V1–V4 to deliver:

GitHub Issue → Repository Analysis → Controlled Repair → Sandbox Tests → Human Approval → GitHub PR.

The owner's explicit V5 authorization supersedes historical V4/V5 stop notices.
It authorizes local engineering and milestones, not remote writes to an unspecified
repository. Stop at V5/V6; no V6 work is authorized.

## Preflight

1. Read AGENTS.md, PROJECT.md, V4 goal, plan and completion report.
2. Verify main, working tree, existing implementation, tests and relevant history.
3. Revalidate V4 core functionality, live PostgreSQL, migrations and Docker Sandbox.
4. Consult current official MCP specification, Python SDK and GitHub MCP Server.
5. Record gaps between frozen V4 profiles and actual GitHub repositories.
6. Create the independent V5 branch and persist actual checks and blockers.

## Architecture boundary

Preserve React, FastAPI, PostgreSQL and V1–V4 retrieval, investigation and
resolution interfaces. Introduce an explicit MCP Client layer using real protocol
discovery and tool calls to the official GitHub MCP Server. The desktop GitHub
connector and direct REST calls alone do not satisfy MCP integration acceptance.

Treat repository files, issues, PRs, comments, server instructions and tool output
as untrusted external data. Application code owns repository, operation, path and
branch authorization. LLM output, tool descriptions and read-only annotations
cannot grant permissions. Keep GitHub credentials out of prompts, logs, persisted
results and Sandbox inputs.

## Scope and requirements

- Bounded, explicitly authorized reading of GitHub repositories, issues and PRs.
- Bind issue identity to canonical repository identity, immutable commit SHA and
  verified Snapshot source. A branch name alone is not an immutable version.
- Reuse the V4 resolution workflow and independent tests only for approved
  executable profiles; reject unsupported repositories before execution.
- Preserve results, actual diffs, source hashes, test revision, test evidence,
  MCP call outcomes and recoverable error states durably.
- Prepare a reviewable publication proposal with exact repository, issue, base
  branch/SHA, dedicated head branch, tested patch/hash, commit and PR metadata.
  Require explicit human approval of that proposal before remote writes. Approval
  is invalid if the approved content, destination or baseline changes.
- Only in an authorized repository, create a dedicated branch, commit the approved
  change and create a PR. Never write the default branch or merge a PR.
- Validate remote baseline, branch ownership/state and effective permissions;
  verify published parent/tree/content against the approved tested proposal.
- Handle repeated requests, concurrent requests, branch collisions, stale bases,
  timeouts and ambiguous remote outcomes without blind mutation retries. Reconcile
  remote state before recovery and retain partial outcomes for human inspection.

## Out of scope

No unrestricted third-party execution, arbitrary shell/dependency installation,
automatic merge, default-branch mutation or unapproved remote writes. No multiple
agents, V6 evaluation platform, V7 deployment/multi-user authentication/queues,
unnecessary V1–V4 refactors or speculative infrastructure.

## Acceptance criteria

1. A real MCP Client connects to the official GitHub MCP Server, discovers tools
   and successfully calls allowed tools; record negotiated protocol and server.
2. A GitHub Issue is linked to the correct repository and immutable code version.
3. Unauthorized repositories, branches and operations cannot acquire write access.
4. A controlled test repository demonstrates the complete repair-to-PR workflow.
5. Remote commit content and baseline match the independently tested patch.
6. Existing V1–V4 behavior and safety boundaries remain effective.
7. Relevant tests, Ruff, migrations and frontend production build pass.
8. Deliver a V5 Completion Report and stop at V5/V6.

Mocked/deterministic tests support implementation verification but cannot replace
actual MCP and GitHub integration evidence. Missing credentials or unavailable
integration checks are explicitly unverified, never passing.

## Execution and escalation

Implement → Test → Self-review → Fix → Verify → Commit → Update Plan → Continue.
Normal milestones are autonomous. Follow AGENTS.md escalation rules for material
architecture conflicts, security issues, missing credentials and remote write
authorization. Do not label V5 complete while required acceptance is outstanding.

The final report must cover changed files, implementation/data flow, dependencies,
actual validation and remote evidence, commits, limitations, risks and scope audit.
