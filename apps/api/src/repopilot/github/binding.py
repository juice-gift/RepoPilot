"""Verified frozen remote bytes → atomic saved Snapshot + immutable provenance."""

import hashlib
import re

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from repopilot.agent.tools import RunScope
from repopilot.config import Settings
from repopilot.db.models import (
    GitHubIssueSnapshot,
    Repository,
    RepositorySnapshot,
    SnapshotFile,
)
from repopilot.github.client import GitHubMCPError, connect_github_readonly
from repopilot.github.fixture_audit import CASES, audit_fixture, embedded_source
from repopilot.github.probe import object_payload
from repopilot.ingestion.scanner import (
    SUPPORTED_LANGUAGES,
    ScannedFile,
    calculate_snapshot_hash,
)
from repopilot.resolution.profiles import TestProfile, load_profile
from repopilot.resolution.workspace import snapshot_sources


def persist_binding(
    session: Session,
    *,
    audit: dict[str, object],
    sources: dict[str, str],
    approved_profiles: list[TestProfile] | None = None,
) -> list[GitHubIssueSnapshot]:
    """Internal trusted orchestration entry; never accepts HTTP/model audit claims."""
    if audit.get("status") != "passed" or not all(audit["checks"].values()):
        raise GitHubMCPError("fixture_not_verified")
    remote_id = audit.get("repository_id")
    commit = audit.get("actual_commit")
    if (
        type(remote_id) is not int
        or remote_id <= 0
        or not isinstance(commit, str)
        or not re.fullmatch(r"[a-f0-9]{40}", commit)
    ):
        raise GitHubMCPError("remote_identity_invalid")
    profiles = approved_profiles or [load_profile(case) for case in CASES]
    for profile in profiles:
        profile.require_snapshot(sources)
        if profile.commit_sha and (
            profile.commit_sha != commit or profile.repository != audit["repository"]
        ):
            raise GitHubMCPError("trusted_binding_scope_mismatch")
    files = tuple(
        ScannedFile(
            path,
            SUPPORTED_LANGUAGES[".md" if path.endswith(".md") else ".py"],
            text,
            hashlib.sha256(text.encode()).hexdigest(),
            len(text.encode()),
        )
        for path, text in sorted(sources.items())
    )
    content_hash = calculate_snapshot_hash(files)
    # Stable non-filesystem identity. No path is read/materialized on the host.
    remote_key = f"github://github.com/repositories/{remote_id}"
    try:
        session.execute(
            insert(Repository)
            .values(name=audit["repository"], local_path=remote_key)
            .on_conflict_do_nothing(index_elements=["local_path"])
        )
        repository = session.scalar(
            select(Repository).where(Repository.local_path == remote_key)
        )
        session.execute(
            insert(RepositorySnapshot)
            .values(
                repository_id=repository.id,
                content_hash=content_hash,
                accepted_file_count=len(files),
                skipped_file_count=0,
                total_bytes=sum(f.byte_size for f in files),
                source_revision=None,
            )
            .on_conflict_do_nothing(index_elements=["repository_id", "content_hash"])
        )
        snapshot = session.scalar(
            select(RepositorySnapshot).where(
                RepositorySnapshot.repository_id == repository.id,
                RepositorySnapshot.content_hash == content_hash,
            )
        )
        for file in files:
            session.execute(
                insert(SnapshotFile)
                .values(
                    snapshot_id=snapshot.id,
                    path=file.path,
                    language=file.language,
                    content_hash=file.content_hash,
                    byte_size=file.byte_size,
                    content=file.content,
                )
                .on_conflict_do_nothing(index_elements=["snapshot_id", "path"])
            )
        saved = snapshot_sources(session, RunScope(repository.id, snapshot.id))
        if {f.path: f.content for f in saved} != sources or any(
            hashlib.sha256(f.content.encode()).hexdigest() != f.content_hash
            for f in saved
        ):
            raise GitHubMCPError("saved_snapshot_integrity_mismatch")
        bindings = []
        for profile, issue in zip(profiles, audit["issues"], strict=True):
            if issue["case"] != profile.case_id or not issue["matches_frozen_contract"]:
                raise GitHubMCPError("issue_contract_mismatch")
            if profile.issue_number and issue["number"] != profile.issue_number:
                raise GitHubMCPError("issue_contract_mismatch")
            body_hash = hashlib.sha256(profile.bound_issue.encode()).hexdigest()
            session.execute(
                insert(GitHubIssueSnapshot)
                .values(
                    remote_repository_id=remote_id,
                    repository_full_name=audit["repository"],
                    commit_sha=commit,
                    issue_number=issue["number"],
                    profile=profile.case_id,
                    issue_body=profile.bound_issue,
                    issue_body_hash=body_hash,
                    snapshot_id=snapshot.id,
                    audit=audit,
                )
                .on_conflict_do_nothing(constraint="uq_github_issue_commit")
            )
            binding = session.scalar(
                select(GitHubIssueSnapshot).where(
                    GitHubIssueSnapshot.remote_repository_id == remote_id,
                    GitHubIssueSnapshot.commit_sha == commit,
                    GitHubIssueSnapshot.issue_number == issue["number"],
                )
            )
            if (
                binding.snapshot_id,
                binding.profile,
                binding.issue_body_hash,
                binding.issue_body,
            ) != (snapshot.id, profile.case_id, body_hash, profile.bound_issue):
                raise GitHubMCPError("binding_conflict")
            bindings.append(binding)
        session.commit()
        return bindings
    except Exception:
        session.rollback()
        raise


async def import_frozen_issues(
    session: Session,
    settings: Settings,
    *,
    repository: str,
    commit: str,
    issue_numbers: tuple[int, int, int],
    expected_login: str,
) -> list[GitHubIssueSnapshot]:
    audit = await audit_fixture(
        settings,
        repository=repository,
        expected_commit=commit,
        issue_numbers=issue_numbers,
        expected_login=expected_login,
    )
    if audit["status"] != "passed":
        raise GitHubMCPError("fixture_not_verified")
    sources = {}
    async with connect_github_readonly(settings) as reader:
        for path in load_profile("fee-days").expected_sources:
            sources[path] = embedded_source(
                await reader.file(repository, path, commit), repository, commit, path
            )
        # Reject a moved branch rather than silently using an unapproved baseline.
        if object_payload(await reader.commit(repository, "main")).get("sha") != commit:
            raise GitHubMCPError("baseline_moved")
    return persist_binding(session, audit=audit, sources=sources)


async def import_trusted_issue(
    session: Session,
    settings: Settings,
    *,
    profile_id: str,
) -> GitHubIssueSnapshot:
    from repopilot.github.fixture_audit import issue_contract
    from repopilot.github.trees import object_hash

    profile = load_profile(
        profile_id,
        registry_path=settings.trusted_profile_registry,
        registry_digest=settings.trusted_profile_registry_sha256,
    )
    if not (
        profile.repository
        and profile.commit_sha
        and profile.issue_number
        and profile.baseline_entries
    ):
        raise GitHubMCPError("trusted_remote_profile_required")
    repository, commit = profile.repository, profile.commit_sha
    async with connect_github_readonly(settings) as reader:
        metadata = object_payload(await reader.repository(repository))
        items = metadata.get("items", [])
        if (
            metadata.get("total_count") != 1
            or len(items) != 1
            or items[0].get("full_name", "").lower() != repository
        ):
            raise GitHubMCPError("repository_identity_mismatch")
        if object_payload(await reader.commit(repository, commit)).get("sha") != commit:
            raise GitHubMCPError("commit_unverified")
        contract = issue_contract(
            await reader.issue(repository, profile.issue_number),
            repository,
            profile.issue_number,
            profile.bound_issue,
        )
        if not contract["matches_frozen_contract"]:
            raise GitHubMCPError("issue_contract_mismatch")
        sources = {}
        for path in profile.expected_sources:
            text = embedded_source(
                await reader.file(repository, path, commit), repository, commit, path
            )
            entry = profile.baseline_entries.get(path, {})
            if entry.get("mode") not in {"100644", "100755"} or entry.get(
                "sha"
            ) != object_hash("blob", text.encode()):
                raise GitHubMCPError("source_tree_mismatch")
            sources[path] = text
        profile.require_snapshot(sources)
        audit = {
            "status": "passed",
            "checks": {"commit_source_issue_verified": True},
            "repository": repository,
            "repository_id": items[0].get("id"),
            "actual_commit": commit,
            "measurement": "actual official MCP trusted Python import",
            "connection": reader.connection_evidence,
            "baseline_tree_sha": profile.baseline_tree_sha,
            "profile_hash": profile.fingerprint(),
            "issues": [{"case": profile.case_id, **contract}],
        }
    return persist_binding(
        session, audit=audit, sources=sources, approved_profiles=[profile]
    )[0]
