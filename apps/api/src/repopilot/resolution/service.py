"""Request lifecycle: immutable DB snapshot → owned workspace → result → cleanup."""

from sqlalchemy.orm import Session

from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.rag.tool_calling import AgentProvider
from repopilot.resolution.models import ResolutionRequest, ResolutionResult
from repopilot.resolution.profiles import TestProfile, load_profile
from repopilot.resolution.runner import run_resolution
from repopilot.resolution.sandbox import SandboxExecutor
from repopilot.resolution.tools import ResolutionLimits, ResolutionTools
from repopilot.resolution.workspace import Workspace, WorkspaceError, snapshot_sources


def resolve_snapshot(
    request: ResolutionRequest,
    *,
    session: Session,
    baseline: ToolRegistry,
    provider: AgentProvider,
    executor: SandboxExecutor,
    limits: ResolutionLimits | None = None,
    approved_profile: TestProfile | None = None,
) -> ResolutionResult:
    scope = RunScope(request.repository_id, request.snapshot_id)
    profile = approved_profile or load_profile(request.profile)
    if profile.case_id != request.profile:
        raise WorkspaceError("Profile identity mismatch")
    if profile.commit_sha:
        from repopilot.intelligence.service import require_snapshot

        snapshot = require_snapshot(session, scope.repository_id, scope.snapshot_id)
        if (
            snapshot.source_revision != profile.commit_sha
            or request.issue != profile.issue
        ):
            raise WorkspaceError("Trusted profile commit or Issue mismatch")
    sources = snapshot_sources(session, scope)
    with Workspace(scope, sources) as workspace:
        root = workspace.root
        tools = ResolutionTools(
            workspace, profile, executor, limits or ResolutionLimits(), baseline
        )
        result = run_resolution(request, tools=tools, provider=provider)
    result.workspace_cleaned = not root.exists()
    return result
