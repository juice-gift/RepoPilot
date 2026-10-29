"""Approval-bound publication, with reconciliation before every possible retry."""

import hashlib
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from repopilot.config import Settings
from repopilot.db.models import GitHubPublication
from repopilot.github.client import GitHubMCPError, connect_github_readonly
from repopilot.github.fixture_audit import embedded_source, issue_contract
from repopilot.github.git_api import (
    GitObjects,
    connect_git_objects,
    require_write_scope,
)
from repopilot.github.pr_client import connect_approved_pr
from repopilot.github.probe import object_payload
from repopilot.github.proposals import PublicationPlan, checked_plan, git_object
from repopilot.resolution.profiles import load_profile


def verify_repository(value: dict, p: PublicationPlan) -> None:
    permissions = value.get("permissions", {})
    if (
        value.get("id") != p.remote_repository_id
        or value.get("full_name") != p.repository
        or value.get("private") is not True
        or value.get("default_branch") != p.base_branch
        or not isinstance(permissions, dict)
        or permissions.get("pull") is not True
        or permissions.get("push") is not True
        or value.get("archived") is True
        or value.get("disabled") is True
    ):
        raise GitHubMCPError("remote_repository_or_permission_mismatch")


def verify_ref(value: dict | None, branch: str, sha: str) -> None:
    if value is None:
        raise GitHubMCPError(
            "baseline_unavailable" if branch == "main" else "branch_unavailable"
        )
    if (
        not isinstance(value, dict)
        or value.get("ref") != f"refs/heads/{branch}"
        or value.get("object", {}).get("type") != "commit"
        or value["object"].get("sha") != sha
    ):
        raise GitHubMCPError(
            "baseline_stale" if branch == "main" else "branch_collision"
        )


def verify_tree(value: dict | None, p: PublicationPlan) -> None:
    if value is None:
        raise GitHubMCPError("remote_tree_unavailable")
    entries = value.get("tree") if isinstance(value, dict) else None
    expected = {
        path: git_object("blob", text.encode()) for path, text in p.files.items()
    }
    if (
        not isinstance(entries, list)
        or value.get("sha") != p.tree_sha
        or value.get("truncated") is not False
        or len(entries) != len(expected)
    ):
        raise GitHubMCPError("remote_tree_mismatch")
    actual = {}
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or entry.get("mode") != "100644"
            or entry.get("type") != "blob"
            or entry.get("path") in actual
        ):
            raise GitHubMCPError("remote_tree_mismatch")
        actual[entry.get("path")] = entry.get("sha")
    if actual != expected:
        raise GitHubMCPError("remote_tree_mismatch")


def verify_commit(value: dict | None, p: PublicationPlan) -> None:
    if value is None:
        raise GitHubMCPError("remote_commit_unavailable")
    if (
        not isinstance(value, dict)
        or value.get("sha") != p.commit_sha
        or value.get("tree", {}).get("sha") != p.tree_sha
        or [v.get("sha") for v in value.get("parents", [])] != [p.base_sha]
        # GitHub renders the message without its terminal LF. The exact object
        # SHA still binds the original complete Git commit bytes.
        or value.get("message")
        not in {p.commit_message, p.commit_message.removesuffix("\n")}
    ):
        raise GitHubMCPError("remote_commit_mismatch")
    for key in ("author", "committer"):
        actor = value.get(key, {})
        if (
            actor.get("name") != p.author_name
            or actor.get("email") != p.author_email
            or datetime.fromisoformat(actor.get("date", ""))
            != datetime.fromisoformat(p.commit_date)
        ):
            raise GitHubMCPError("remote_commit_mismatch")


def verify_pr(value: dict, p: PublicationPlan) -> tuple[int, str]:
    number = value.get("number")
    if type(number) is not int or number < 1:
        raise GitHubMCPError("pr_identity_invalid")
    url = f"https://github.com/{p.repository}/pull/{number}"
    if (
        value.get("title") != p.pr_title
        or value.get("body") != p.pr_body
        or value.get("draft") is not True
        or value.get("merged") is not False
        or value.get("state") != "open"
        or value.get("html_url") != url
    ):
        raise GitHubMCPError("pr_content_mismatch")
    for key, branch, sha in (
        ("head", p.head_branch, p.commit_sha),
        ("base", p.base_branch, p.base_sha),
    ):
        ref = value.get(key, {})
        if (
            ref.get("ref") != branch
            or ref.get("sha") != sha
            or ref.get("repo", {}).get("full_name") != p.repository
        ):
            raise GitHubMCPError("pr_ref_mismatch")
    return number, url


async def readonly_preflight(settings: Settings, p: PublicationPlan) -> dict:
    async with connect_github_readonly(settings) as reader:
        if (
            object_payload(await reader.identity()).get("login")
            != p.repository.split("/")[0]
        ):
            raise GitHubMCPError("identity_mismatch")
        metadata = object_payload(await reader.repository(p.repository))
        items = metadata.get("items")
        if (
            metadata.get("total_count") != 1
            or not isinstance(items, list)
            or len(items) != 1
        ):
            raise GitHubMCPError("repository_unverified")
        verify_repository(items[0], p)
        if (
            object_payload(await reader.commit(p.repository, "main")).get("sha")
            != p.base_sha
        ):
            raise GitHubMCPError("baseline_stale")
        root = (await reader.file(p.repository, "", p.base_sha)).data.get(
            "structured_content"
        )
        if (
            not isinstance(root, list)
            or len(root) != len(p.files)
            or {
                e.get("path")
                for e in root
                if isinstance(e, dict) and e.get("type") == "file"
            }
            != set(p.files)
        ):
            raise GitHubMCPError("remote_baseline_source_mismatch")
        for path, digest in p.baseline_hashes.items():
            source = embedded_source(
                await reader.file(p.repository, path, p.base_sha),
                p.repository,
                p.base_sha,
                path,
            )
            if hashlib.sha256(source.encode()).hexdigest() != digest:
                raise GitHubMCPError("remote_baseline_source_mismatch")
        contract = issue_contract(
            await reader.issue(p.repository, p.issue_number),
            p.repository,
            p.issue_number,
            load_profile(p.profile).issue,
        )
        if not contract["matches_frozen_contract"]:
            raise GitHubMCPError("remote_issue_changed")
        return reader.connection_evidence


async def require_baseline(git: GitObjects, p: PublicationPlan) -> None:
    verify_ref(await git.ref("main"), "main", p.base_sha)


async def publish_effects(
    settings: Settings, p: PublicationPlan, digest: str, outcome: dict
) -> None:
    outcome["readonly_preflight"] = await readonly_preflight(settings, p)
    async with connect_git_objects(settings, p, digest) as git:
        verify_repository(await git.metadata(), p)
        await require_baseline(git, p)
        baseline = await git.commit(baseline=True)
        if (
            baseline is None
            or baseline.get("sha") != p.base_sha
            or baseline.get("tree", {}).get("sha") != p.baseline_tree_sha
        ):
            raise GitHubMCPError("remote_baseline_tree_mismatch")
        branch = await git.ref(p.head_branch)
        if branch is not None:
            verify_ref(branch, p.head_branch, p.commit_sha)
        # Read by deterministic object identity before any create/retry. A timeout
        # exits; a subsequent request must reconcile again, never blindly retry.
        tree = await git.tree()
        if tree is None:
            await require_baseline(git, p)
            created = await git.create_tree()
            observed = created.get("sha")
            if isinstance(observed, str) and re.fullmatch(r"[a-f0-9]{40}", observed):
                outcome["observed_tree_sha"] = observed
            if created.get("sha") != p.tree_sha:
                raise GitHubMCPError("remote_tree_mismatch")
            # GitHub may not expose an unreferenced object through GET yet. The
            # create response carries the full tree: verify it before creating
            # the exact commit; require reachable GET readback before a PR.
            tree = created
        verify_tree(tree, p)
        outcome["tree_sha"] = p.tree_sha
        commit = await git.commit()
        if commit is None:
            await require_baseline(git, p)
            created = await git.create_commit()
            observed = created.get("sha")
            if isinstance(observed, str) and re.fullmatch(r"[a-f0-9]{40}", observed):
                outcome["observed_commit_sha"] = observed
            if created.get("sha") != p.commit_sha:
                raise GitHubMCPError("remote_commit_mismatch")
            commit = created
        verify_commit(commit, p)
        outcome["commit_sha"] = p.commit_sha
        if branch is None:
            await require_baseline(git, p)
            await git.create_branch()
        verify_ref(await git.ref(p.head_branch), p.head_branch, p.commit_sha)
        outcome["branch"] = p.head_branch
        verify_commit(await git.commit(), p)
        verify_tree(await git.tree(), p)
        await require_baseline(git, p)
        async with connect_approved_pr(settings, p, digest) as prs:
            outcome["pr_connection"] = prs.connection_evidence
            matches = await prs.find()
            if not matches:
                await require_baseline(git, p)
                verify_ref(await git.ref(p.head_branch), p.head_branch, p.commit_sha)
                await prs.create()
                matches = await prs.find()
            if len(matches) != 1:
                raise GitHubMCPError("pr_outcome_unresolved")
            number = matches[0].get("number")
            # Preserve known identity even if later content/baseline verification fails.
            if type(number) is int and number > 0:
                outcome["observed_pr_number"] = number
                outcome["observed_pr_url"] = (
                    f"https://github.com/{p.repository}/pull/{number}"
                )
            number, url = verify_pr(await prs.get(number), p)
            outcome.update(
                pr_number=number,
                pr_url=url,
                pr_transport="official GitHub MCP",
                requested_maintainer_can_modify=False,
            )
        await require_baseline(git, p)
        verify_ref(await git.ref(p.head_branch), p.head_branch, p.commit_sha)
        verify_commit(await git.commit(), p)
        verify_tree(await git.tree(), p)
        outcome.update(
            parent_sha=p.base_sha,
            exact_content_verified=True,
            default_branch_unchanged=True,
        )


async def publish_proposal(
    session: Session, settings: Settings, identifier: str
) -> GitHubPublication:
    def locked() -> GitHubPublication:
        try:
            row = session.scalar(
                select(GitHubPublication)
                .where(GitHubPublication.id == identifier)
                .with_for_update(nowait=True)
                .execution_options(populate_existing=True)
            )
        except SQLAlchemyError:
            session.rollback()
            raise GitHubMCPError("publication_busy_or_database_unavailable") from None
        if row is None:
            raise GitHubMCPError("proposal_not_found")
        return row

    row = locked()
    plan = checked_plan(session, settings, row)
    require_write_scope(settings, plan, row.approved_hash)
    if row.state == "published":
        # Idempotent response: historical verified outcome, no additional writes.
        session.rollback()
        return session.get(GitHubPublication, identifier)
    if row.state not in {"approved", "publishing", "retry_needed"}:
        raise GitHubMCPError("proposal_state_denied")
    row.state, row.last_error = "publishing", None
    session.commit()  # Durable crash marker before side effects.
    row = locked()  # Hold the DB row lock for the entire remote operation.
    plan = checked_plan(session, settings, row)
    require_write_scope(settings, plan, row.approved_hash)
    if row.state == "published":
        session.rollback()
        return session.get(GitHubPublication, identifier)
    if row.state != "publishing":
        raise GitHubMCPError("proposal_state_denied")
    outcome = dict(row.outcome)
    try:
        await publish_effects(settings, plan, row.plan_hash, outcome)
        row.state, row.last_error = "published", None
    except Exception as exc:  # noqa: BLE001 - retain only safe errors, never SDK payloads
        code = (
            exc.code
            if isinstance(exc, GitHubMCPError)
            else "publication_failed_ambiguous"
        )
        stale = code in {
            "baseline_stale",
            "remote_issue_changed",
            "branch_collision",
            "remote_repository_or_permission_mismatch",
            "remote_baseline_tree_mismatch",
            "remote_baseline_source_mismatch",
            "remote_tree_mismatch",
            "remote_commit_mismatch",
            "pr_collision",
            "pr_content_mismatch",
            "pr_ref_mismatch",
        }
        row.state, row.last_error = ("stale" if stale else "retry_needed"), code
        if stale:
            row.approved_hash = None
    row.outcome = outcome
    session.commit()
    return row
