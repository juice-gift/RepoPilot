"""Request lifecycle: immutable DB snapshot → owned workspace → result → cleanup."""

from sqlalchemy.orm import Session

from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.rag.tool_calling import AgentProvider
from repopilot.resolution.models import ResolutionRequest, ResolutionResult
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.runner import run_resolution
from repopilot.resolution.sandbox import SandboxExecutor
from repopilot.resolution.tools import ResolutionLimits, ResolutionTools
from repopilot.resolution.workspace import Workspace, snapshot_sources


def resolve_snapshot(
    request: ResolutionRequest,
    *,
    session: Session,
    baseline: ToolRegistry,
    provider: AgentProvider,
    executor: SandboxExecutor,
    limits: ResolutionLimits | None = None,
) -> ResolutionResult:
    scope = RunScope(request.repository_id, request.snapshot_id)
    profile = load_profile(request.profile)
    sources = snapshot_sources(session, scope)
    with Workspace(scope, sources) as workspace:
        root = workspace.root
        tools = ResolutionTools(
            workspace, profile, executor, limits or ResolutionLimits(), baseline
        )
        result = run_resolution(request, tools=tools, provider=provider)
    result.workspace_cleaned = not root.exists()
    return result
