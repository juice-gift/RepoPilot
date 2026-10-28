"""Synchronous controlled repair of a server-owned Issue/Snapshot binding."""

import hashlib
import json
from collections.abc import Callable
from uuid import uuid4

from sqlalchemy.orm import Session

from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.config import Settings
from repopilot.db.models import (
    GitHubIssueSnapshot,
    GitHubResolutionRun,
    RepositorySnapshot,
)
from repopilot.embeddings.providers import EmbeddingProvider
from repopilot.github.client import GitHubMCPError
from repopilot.indexing.service import index_snapshot
from repopilot.intelligence.service import index_structure
from repopilot.rag.tool_calling import AgentProvider
from repopilot.resolution.models import ResolutionRequest
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxExecutor
from repopilot.resolution.service import resolve_snapshot
from repopilot.resolution.workspace import snapshot_sources


def result_hash(result: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            result, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def resolve_bound_issue(
    session: Session,
    settings: Settings,
    *,
    binding_id: int,
    provider: AgentProvider,
    executor: SandboxExecutor,
    embedding_factory: Callable[[], EmbeddingProvider],
) -> GitHubResolutionRun:
    binding = session.get(GitHubIssueSnapshot, binding_id)
    if (
        binding is None
        or binding.repository_full_name.lower()
        not in settings.github_mcp_allowed_repositories
    ):
        raise GitHubMCPError("binding_denied")
    profile = load_profile(binding.profile)
    if (
        binding.issue_body != profile.issue
        or binding.issue_body_hash != hashlib.sha256(profile.issue.encode()).hexdigest()
    ):
        raise GitHubMCPError("binding_integrity_mismatch")
    snapshot = session.get(RepositorySnapshot, binding.snapshot_id)
    if snapshot is None:
        raise GitHubMCPError("snapshot_unavailable")
    scope = RunScope(snapshot.repository_id, snapshot.id)
    before = snapshot_sources(session, scope)
    profile.require_snapshot({f.path: f.content for f in before})
    request = ResolutionRequest(
        repository_id=scope.repository_id,
        snapshot_id=scope.snapshot_id,
        profile=profile.case_id,
        issue=binding.issue_body,
    )
    run = GitHubResolutionRun(id=uuid4().hex, binding_id=binding.id, state="running")
    session.add(run)
    session.commit()
    try:
        index_structure(
            session, repository_id=scope.repository_id, snapshot_id=scope.snapshot_id
        )
        index_snapshot(
            session,
            repository_id=scope.repository_id,
            snapshot_id=scope.snapshot_id,
            provider=embedding_factory(),
        )
        result = resolve_snapshot(
            request,
            session=session,
            baseline=ToolRegistry(session, scope, embedding_factory=embedding_factory),
            provider=provider,
            executor=executor,
        )
        if snapshot_sources(session, scope) != before:
            raise GitHubMCPError("snapshot_changed_during_resolution")
        encoded = result.model_dump(mode="json")
        run.result = encoded
        run.result_hash = result_hash(encoded)
        run.state = "completed"
        session.commit()
        return run
    except Exception:  # noqa: BLE001 - persist safe failure without SDK/credential details
        session.rollback()
        run.state = "failed"
        run.failure = "resolution_failed"
        session.commit()
        raise GitHubMCPError("resolution_failed") from None
