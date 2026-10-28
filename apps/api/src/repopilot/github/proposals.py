"""Server-derived immutable publication plans; no remote mutation here."""

import hashlib
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from repopilot.agent.tools import RunScope
from repopilot.config import Settings
from repopilot.db.models import (
    GitHubIssueSnapshot,
    GitHubPublication,
    GitHubResolutionRun,
    RepositorySnapshot,
)
from repopilot.github.client import GitHubMCPError
from repopilot.github.resolution import result_hash
from repopilot.resolution.models import ResolutionResult
from repopilot.resolution.patch import source_diff
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.workspace import snapshot_sources


def git_object(kind: str, content: bytes) -> str:
    # Git SHA1 object identity, not a cryptographic authorization primitive.
    return hashlib.sha1(f"{kind} {len(content)}\0".encode() + content).hexdigest()


def tree_hash(files: dict[str, str]) -> str:
    if any("/" in path or "\0" in path for path in files):
        raise GitHubMCPError("only_flat_frozen_tree_supported")
    data = b"".join(
        b"100644 "
        + path.encode()
        + b"\0"
        + bytes.fromhex(git_object("blob", text.encode()))
        for path, text in sorted(files.items())
    )
    return git_object("tree", data)


class PublicationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    proposal_id: str
    run_id: str
    result_hash: str
    repository: str
    remote_repository_id: int
    issue_number: int
    profile: str
    snapshot_id: int
    base_branch: Literal["main"] = "main"
    base_sha: str
    head_branch: str
    files: dict[str, str]
    baseline_hashes: dict[str, str]
    changed_paths: list[str]
    diff: str
    tree_sha: str
    commit_sha: str
    commit_message: str
    commit_date: str
    author_name: str = "RepoPilot"
    author_email: str = "repopilot@users.noreply.github.com"
    pr_title: str
    pr_body: str
    draft: Literal[True] = True
    test_passed: int
    tested_revision: int


def commit_hash(tree: str, parent: str, message: str, date: str) -> str:
    epoch = int(datetime.fromisoformat(date).timestamp())
    actor = f"RepoPilot <repopilot@users.noreply.github.com> {epoch} +0000"
    raw = (
        f"tree {tree}\nparent {parent}\nauthor {actor}\ncommitter {actor}\n\n{message}"
    )
    return git_object("commit", raw.encode())


def verified_run(
    session: Session, settings: Settings, run_id: str
) -> tuple[GitHubResolutionRun, GitHubIssueSnapshot, dict[str, str], ResolutionResult]:
    run = session.get(GitHubResolutionRun, run_id)
    if (
        run is None
        or run.state != "completed"
        or run.result is None
        or result_hash(run.result) != run.result_hash
    ):
        raise GitHubMCPError("run_not_verified")
    binding = session.get(GitHubIssueSnapshot, run.binding_id)
    if (
        binding is None
        or binding.repository_full_name not in settings.github_mcp_allowed_repositories
    ):
        raise GitHubMCPError("repository_denied")
    profile = load_profile(binding.profile)
    if (
        binding.issue_body != profile.issue
        or hashlib.sha256(binding.issue_body.encode()).hexdigest()
        != binding.issue_body_hash
    ):
        raise GitHubMCPError("binding_integrity_mismatch")
    snapshot = session.get(RepositorySnapshot, binding.snapshot_id)
    if snapshot is None:
        raise GitHubMCPError("snapshot_unavailable")
    source = {
        f.path: f.content
        for f in snapshot_sources(
            session, RunScope(snapshot.repository_id, snapshot.id)
        )
    }
    profile.require_snapshot(source)
    result = ResolutionResult.model_validate(run.result)
    if (result.repository_id, result.snapshot_id, result.profile) != (
        snapshot.repository_id,
        snapshot.id,
        binding.profile,
    ):
        raise GitHubMCPError("run_scope_mismatch")
    if (
        result.repair_status != "verified_repair"
        or result.execution_status != "completed"
        or result.stop_reason != "completed"
        or not result.workspace_cleaned
        or result.revision < 1
    ):
        raise GitHubMCPError("repair_not_publishable")
    baseline = [
        t
        for t in result.test_results
        if t.revision == 0
        and t.profile == profile.case_id
        and t.workspace_id == result.workspace_id
        and t.expected_tests == profile.expected_tests
        and t.isolation_confirmed
        and t.cleanup_confirmed
        and not t.timed_out
        and not t.truncated
        and not t.infrastructure_error
        and t.exit_code == 1
        and t.observed_passed == profile.expected_tests - profile.baseline_failures
    ]
    tested = [
        t
        for t in result.test_results
        if t.revision == result.revision
        and t.passed
        and t.expected_tests == profile.expected_tests
        and t.profile == profile.case_id
        and t.workspace_id == result.workspace_id
    ]
    changed = [f.path for f in result.changed_files]
    if (
        not baseline
        or not tested
        or not changed
        or len(changed) != len(set(changed))
        or not set(changed) <= profile.editable_paths
    ):
        raise GitHubMCPError("test_or_patch_not_verified")
    modified = dict(source)
    for file in result.changed_files:
        if file.original != source[file.path] or file.original == file.modified:
            raise GitHubMCPError("patch_source_mismatch")
        modified[file.path] = file.modified
    if source_diff(source, modified) != result.patch:
        raise GitHubMCPError("diff_mismatch")
    return run, binding, source, result


def build_plan(
    session: Session, settings: Settings, run_id: str, proposal_id: str, date: str
) -> PublicationPlan:
    run, binding, source, result = verified_run(session, settings, run_id)
    files = dict(source)
    for changed in result.changed_files:
        files[changed.path] = changed.modified
    tree = tree_hash(files)
    message = f"fix: resolve issue #{binding.issue_number} ({binding.profile})\n\nRepoPilot proposal {proposal_id}\n"
    body = (
        f"Controlled repair for #{binding.issue_number}.\n\n"
        f"Base: `{binding.commit_sha}`\nSnapshot: `{binding.snapshot_id}`\n"
        f"Result: `{run.result_hash}`\nIndependent tests: {load_profile(binding.profile).expected_tests} passed at revision {result.revision}.\n\n"
        f"RepoPilot-Proposal: {proposal_id}\n\nHuman review required. No merge is authorized.\n"
    )
    return PublicationPlan(
        proposal_id=proposal_id,
        run_id=run.id,
        result_hash=run.result_hash,
        repository=binding.repository_full_name,
        remote_repository_id=binding.remote_repository_id,
        issue_number=binding.issue_number,
        profile=binding.profile,
        snapshot_id=binding.snapshot_id,
        base_sha=binding.commit_sha,
        head_branch=f"codex/issue-{binding.issue_number}-{proposal_id}",
        files=files,
        baseline_hashes={
            p: hashlib.sha256(t.encode()).hexdigest() for p, t in source.items()
        },
        changed_paths=sorted(f.path for f in result.changed_files),
        diff=result.patch,
        tree_sha=tree,
        commit_sha=commit_hash(tree, binding.commit_sha, message, date),
        commit_message=message,
        commit_date=date,
        pr_title=f"Fix issue #{binding.issue_number}: {binding.profile}",
        pr_body=body,
        test_passed=load_profile(binding.profile).expected_tests,
        tested_revision=result.revision,
    )


def checked_plan(
    session: Session, settings: Settings, row: GitHubPublication
) -> PublicationPlan:
    plan = PublicationPlan.model_validate(row.plan)
    rebuilt = build_plan(session, settings, row.run_id, row.id, plan.commit_date)
    if plan != rebuilt or result_hash(plan.model_dump(mode="json")) != row.plan_hash:
        raise GitHubMCPError("proposal_integrity_mismatch")
    return plan


def prepare_proposal(
    session: Session, settings: Settings, run_id: str
) -> GitHubPublication:
    existing = session.scalar(
        select(GitHubPublication).where(GitHubPublication.run_id == run_id)
    )
    if existing:
        checked_plan(session, settings, existing)
        return existing
    identifier = uuid4().hex
    plan = build_plan(
        session,
        settings,
        run_id,
        identifier,
        datetime.now(UTC).replace(microsecond=0).isoformat(),
    )
    payload = plan.model_dump(mode="json")
    session.execute(
        insert(GitHubPublication)
        .values(
            id=identifier,
            run_id=run_id,
            plan=payload,
            plan_hash=result_hash(payload),
            state="awaiting_approval",
            outcome={},
        )
        .on_conflict_do_nothing(index_elements=["run_id"])
    )
    session.commit()
    row = session.scalar(
        select(GitHubPublication).where(GitHubPublication.run_id == run_id)
    )
    checked_plan(session, settings, row)
    return row


def approve_proposal(
    session: Session,
    settings: Settings,
    identifier: str,
    expected_hash: str,
    confirmation: str,
) -> GitHubPublication:
    row = session.scalar(
        select(GitHubPublication)
        .where(GitHubPublication.id == identifier)
        .with_for_update(nowait=True)
    )
    if row is None:
        raise GitHubMCPError("proposal_not_found")
    checked_plan(session, settings, row)
    if (
        expected_hash != row.plan_hash
        or confirmation != f"APPROVE {identifier}:{row.plan_hash}"
    ):
        raise GitHubMCPError("approval_mismatch")
    if row.state not in {"awaiting_approval", "approved"}:
        raise GitHubMCPError("proposal_state_denied")
    row.approved_hash, row.state = row.plan_hash, "approved"
    session.commit()
    return row
