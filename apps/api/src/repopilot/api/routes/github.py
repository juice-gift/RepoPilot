"""Thin local-owner GitHub workflow API. No LLM can approve a publication."""

from functools import partial
from typing import Annotated

import anyio
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.db.models import (
    GitHubIssueSnapshot,
    GitHubPublication,
    GitHubResolutionRun,
)
from repopilot.embeddings.providers import create_embedding_provider
from repopilot.github.binding import import_frozen_issues
from repopilot.github.client import GitHubMCPError
from repopilot.github.proposals import (
    PublicationPlan,
    approve_proposal,
    checked_plan,
    prepare_proposal,
)
from repopilot.github.resolution import resolve_bound_issue
from repopilot.rag.generation import create_agent_provider
from repopilot.resolution.models import ResolutionResult
from repopilot.resolution.sandbox import SandboxExecutor

router = APIRouter(prefix="/api/github", tags=["github"])
DB = Annotated[Session, Depends(get_database_session)]


class BindingView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    repository_full_name: str
    issue_number: int
    commit_sha: str
    snapshot_id: int
    profile: str


class RunView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    binding_id: int
    state: str
    result: ResolutionResult | None
    result_hash: str | None
    failure: str | None


class ProposalView(BaseModel):
    id: str
    plan: PublicationPlan
    plan_hash: str
    state: str
    approved: bool
    outcome: dict[str, object]
    last_error: str | None


def proposal_view(
    row: GitHubPublication, session: Session, request: Request
) -> ProposalView:
    plan = checked_plan(session, request.app.state.settings, row)
    return ProposalView(
        id=row.id,
        plan=plan,
        plan_hash=row.plan_hash,
        state=row.state,
        approved=row.approved_hash == row.plan_hash,
        outcome=row.outcome,
        last_error=row.last_error,
    )


def owner_control(request: Request) -> None:
    if (
        request.client is None
        or request.client.host not in {"127.0.0.1", "::1"}
        or request.headers.get("origin") != request.app.state.settings.frontend_origin
    ):
        raise HTTPException(
            403, "Approval and publication require the local owner's configured origin"
        )


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repository: str = Field(min_length=3, max_length=140)
    commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    issue_numbers: tuple[int, int, int]


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    binding_id: int = Field(gt=0)


class ProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(pattern=r"^[a-f0-9]{32}$")


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmation: str = Field(max_length=160)


@router.get("/bindings", response_model=list[BindingView])
def bindings(request: Request, session: DB):
    return session.scalars(
        select(GitHubIssueSnapshot)
        .where(
            GitHubIssueSnapshot.repository_full_name.in_(
                request.app.state.settings.github_mcp_allowed_repositories
            )
        )
        .order_by(GitHubIssueSnapshot.id.desc())
        .limit(50)
    ).all()


@router.post("/import", response_model=list[BindingView])
def import_issues(payload: ImportRequest, request: Request, session: DB):
    owner_control(request)
    try:
        return anyio.run(
            partial(
                import_frozen_issues,
                session,
                request.app.state.settings,
                repository=payload.repository,
                commit=payload.commit,
                issue_numbers=payload.issue_numbers,
                expected_login=payload.repository.split("/")[0],
            )
        )
    except GitHubMCPError as exc:
        raise HTTPException(409, exc.code) from None


@router.get("/runs", response_model=list[RunView])
def runs(request: Request, session: DB):
    return session.scalars(
        select(GitHubResolutionRun)
        .join(GitHubIssueSnapshot)
        .where(
            GitHubIssueSnapshot.repository_full_name.in_(
                request.app.state.settings.github_mcp_allowed_repositories
            )
        )
        .order_by(GitHubResolutionRun.created_at.desc())
        .limit(50)
    ).all()


@router.post("/runs", response_model=RunView)
def resolve(payload: RunRequest, request: Request, session: DB):
    owner_control(request)
    settings = request.app.state.settings
    if not settings.resolution_sandbox_image:
        raise HTTPException(503, "Configure the approved immutable Sandbox image")
    try:
        return resolve_bound_issue(
            session,
            settings,
            binding_id=payload.binding_id,
            provider=create_agent_provider(settings),
            executor=SandboxExecutor(settings.resolution_sandbox_image),
            embedding_factory=lambda: create_embedding_provider(settings),
        )
    except GitHubMCPError as exc:
        raise HTTPException(409, exc.code) from None


@router.post("/proposals", response_model=ProposalView)
def propose(payload: ProposalRequest, request: Request, session: DB):
    owner_control(request)
    try:
        return proposal_view(
            prepare_proposal(session, request.app.state.settings, payload.run_id),
            session,
            request,
        )
    except GitHubMCPError as exc:
        raise HTTPException(409, exc.code) from None


@router.get("/proposals/{identifier}", response_model=ProposalView)
def get_proposal(identifier: str, request: Request, session: DB):
    row = session.get(GitHubPublication, identifier)
    if row is None:
        raise HTTPException(404, "Proposal not found")
    try:
        return proposal_view(row, session, request)
    except GitHubMCPError as exc:
        raise HTTPException(409, exc.code) from None


@router.post("/proposals/{identifier}/approve", response_model=ProposalView)
def approve(identifier: str, payload: ApprovalRequest, request: Request, session: DB):
    owner_control(request)
    try:
        row = approve_proposal(
            session,
            request.app.state.settings,
            identifier,
            payload.expected_hash,
            payload.confirmation,
        )
        return proposal_view(row, session, request)
    except GitHubMCPError as exc:
        raise HTTPException(409, exc.code) from None
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(409, "Proposal is busy or database unavailable") from None


@router.post("/proposals/{identifier}/revoke", response_model=ProposalView)
def revoke(identifier: str, request: Request, session: DB):
    owner_control(request)
    row = session.scalar(
        select(GitHubPublication)
        .where(GitHubPublication.id == identifier)
        .with_for_update(nowait=True)
    )
    if row is None or row.state not in {"awaiting_approval", "approved"}:
        raise HTTPException(
            409, "Cannot revoke a publication that may have remote effects"
        )
    row.approved_hash, row.state = None, "awaiting_approval"
    session.commit()
    return proposal_view(row, session, request)
