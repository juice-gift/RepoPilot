"""Deterministic publication fault injection; not live GitHub acceptance evidence."""

import copy
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import anyio
import httpx2
import pytest
from mcp.types import CallToolResult
from sqlalchemy.orm import Session
from test_github_proposals import (
    saved_repair as saved_repair_fixture,
)

from repopilot.github.client import GitHubMCPError
from repopilot.github.git_api import GitObjects, require_write_scope
from repopilot.github.pr_client import (
    PR_TOOLS,
    ApprovedPRClient,
    connect_approved_pr,
    inspect_pr_support,
)
from repopilot.github.proposals import (
    approve_proposal,
    checked_plan,
    git_object,
    prepare_proposal,
)
from repopilot.github.publication import (
    publish_proposal,
    verify_commit,
    verify_pr,
    verify_tree,
)


def ref(branch, sha):
    return {"ref": f"refs/heads/{branch}", "object": {"type": "commit", "sha": sha}}


saved_repair = saved_repair_fixture


class Remote:
    def __init__(self, plan, fail_after=None):
        self.connection_evidence = {"measurement": "fault injection only"}
        self.p = plan
        self.fail_after = fail_after
        self.events = []
        self.refs = {"main": ref("main", plan.base_sha)}
        self.trees = {}
        self.commits = {}
        self.prs = []
        self.metadata_value = {
            "id": plan.remote_repository_id,
            "full_name": plan.repository,
            "default_branch": "main",
            "private": True,
            "permissions": {"pull": True, "push": True},
        }

    def event(self, name):
        self.events.append(name)
        if name == self.fail_after:
            self.fail_after = None
            raise GitHubMCPError("timeout_ambiguous")

    async def metadata(self):
        return self.metadata_value

    async def ref(self, branch):
        return self.refs.get(branch)

    async def tree(self):
        if (
            getattr(self, "hide_unreferenced", False)
            and self.p.head_branch not in self.refs
        ):
            return None
        return self.trees.get(self.p.tree_sha)

    async def commit(self, *, baseline=False):
        if baseline:
            return {"sha": self.p.base_sha, "tree": {"sha": self.p.baseline_tree_sha}}
        if (
            getattr(self, "hide_unreferenced", False)
            and self.p.head_branch not in self.refs
        ):
            return None
        return self.commits.get(self.p.commit_sha)

    async def create_tree(self):
        result = {
            "sha": self.p.tree_sha,
            "truncated": False,
            "tree": [
                {
                    "path": k,
                    "type": "blob",
                    "mode": "100644",
                    "sha": git_object("blob", v.encode()),
                }
                for k, v in self.p.files.items()
            ],
        }
        self.trees[self.p.tree_sha] = result
        self.event("tree")
        return result

    async def create_commit(self):
        actor = {
            "name": self.p.author_name,
            "email": self.p.author_email,
            "date": self.p.commit_date,
        }
        result = {
            "sha": self.p.commit_sha,
            "tree": {"sha": self.p.tree_sha},
            "parents": [{"sha": self.p.base_sha}],
            "message": self.p.commit_message,
            "author": actor,
            "committer": actor,
        }
        self.commits[self.p.commit_sha] = result
        self.event("commit")
        return result

    async def create_branch(self):
        assert self.p.head_branch not in self.refs
        self.refs[self.p.head_branch] = ref(self.p.head_branch, self.p.commit_sha)
        self.event("branch")
        return self.refs[self.p.head_branch]

    async def find(self):
        if len(self.prs) > 1:
            raise GitHubMCPError("pr_collision")
        return self.prs

    async def get(self, number):
        assert self.prs[0]["number"] == number
        return self.prs[0]

    async def create(self):
        assert not self.prs
        p = self.p
        self.prs.append(
            {
                "number": 41,
                "title": p.pr_title,
                "body": p.pr_body,
                "draft": True,
                "merged": False,
                "state": "open",
                "html_url": f"https://github.com/{p.repository}/pull/41",
                "head": {
                    "ref": p.head_branch,
                    "sha": p.commit_sha,
                    "repo": {"full_name": p.repository},
                },
                "base": {
                    "ref": "main",
                    "sha": p.base_sha,
                    "repo": {"full_name": p.repository},
                },
            }
        )
        self.event("pr")


def setup(saved, monkeypatch, *, fail_after=None, approve=True):
    session, config, run = saved
    row = prepare_proposal(session, config, run.id)
    if approve:
        approve_proposal(
            session, config, row.id, row.plan_hash, f"APPROVE {row.id}:{row.plan_hash}"
        )
    config.github_write_allowed_repositories = config.github_mcp_allowed_repositories
    remote = Remote(checked_plan(session, config, row), fail_after)

    @asynccontextmanager
    async def connection(settings, plan, digest):
        require_write_scope(settings, plan, digest)
        yield remote

    async def preflight(*args):
        return {"measurement": "fault injection only"}

    monkeypatch.setattr("repopilot.github.publication.connect_git_objects", connection)
    monkeypatch.setattr("repopilot.github.publication.connect_approved_pr", connection)
    monkeypatch.setattr("repopilot.github.publication.readonly_preflight", preflight)
    return session, config, row, remote


@pytest.mark.parametrize("failure", [None, "tree", "commit", "branch", "pr"])
def test_publish_reconciles_ambiguous_success_and_repeats_without_duplication(
    saved_repair, monkeypatch, failure
):
    session, config, row, remote = setup(saved_repair, monkeypatch, fail_after=failure)
    first = anyio.run(publish_proposal, session, config, row.id)
    if failure:
        assert first.state == "retry_needed" and first.last_error == "timeout_ambiguous"
        first = anyio.run(publish_proposal, session, config, row.id)
    assert first.state == "published"
    assert first.outcome["exact_content_verified"] and first.outcome["pr_number"] == 41
    assert remote.events == ["tree", "commit", "branch", "pr"]
    repeated = anyio.run(publish_proposal, session, config, row.id)
    assert repeated.state == "published" and remote.events == [
        "tree",
        "commit",
        "branch",
        "pr",
    ]
    assert remote.refs["main"]["object"]["sha"] == remote.p.base_sha


@pytest.mark.parametrize(
    "bad",
    [
        "no_approval",
        "repo_denied",
        "baseline",
        "collision",
        "permissions",
        "repository_id",
        "pr_collision",
        "pr_tamper",
    ],
)
def test_publication_denials(saved_repair, monkeypatch, bad):
    session, config, row, remote = setup(
        saved_repair, monkeypatch, approve=bad != "no_approval"
    )
    if bad == "repo_denied":
        config.github_write_allowed_repositories = []
    elif bad == "baseline":
        remote.refs["main"] = ref("main", "a" * 40)
    elif bad == "collision":
        remote.refs[remote.p.head_branch] = ref(remote.p.head_branch, "b" * 40)
    elif bad == "permissions":
        remote.metadata_value["permissions"]["push"] = False
    elif bad == "repository_id":
        remote.metadata_value["id"] += 1
    elif bad in {"pr_collision", "pr_tamper"}:
        awaitable = remote.create()
        anyio.run(lambda: awaitable)
        remote.events.clear()
        if bad == "pr_collision":
            remote.prs.append(copy.deepcopy(remote.prs[0]))
        else:
            remote.prs[0]["body"] = "unapproved text"
    if bad in {"no_approval", "repo_denied"}:
        with pytest.raises(GitHubMCPError, match="not_authorized"):
            anyio.run(publish_proposal, session, config, row.id)
        session.rollback()
    else:
        result = anyio.run(publish_proposal, session, config, row.id)
        assert result.state == "stale" and result.approved_hash is None
    assert "pr" not in remote.events
    if bad not in {"pr_collision", "pr_tamper"}:
        assert remote.events == []


def test_concurrent_publisher_denied_while_row_locked(saved_repair, monkeypatch):
    session, config, row, remote = setup(saved_repair, monkeypatch)
    session.refresh(row, with_for_update=True)
    with (
        Session(session.get_bind()) as concurrent,
        pytest.raises(GitHubMCPError, match="busy"),
    ):
        anyio.run(publish_proposal, concurrent, config, row.id)
    session.rollback()
    assert remote.events == []


def test_unreferenced_objects_verified_from_create_then_reachable_readback(
    saved_repair, monkeypatch
):
    session, config, row, remote = setup(saved_repair, monkeypatch)
    remote.hide_unreferenced = True
    result = anyio.run(publish_proposal, session, config, row.id)
    assert result.state == "published"
    assert remote.events == ["tree", "commit", "branch", "pr"]


def test_crash_marker_can_reconcile(saved_repair, monkeypatch):
    session, config, row, _ = setup(saved_repair, monkeypatch)
    row.state = "publishing"
    session.commit()
    assert anyio.run(publish_proposal, session, config, row.id).state == "published"


@pytest.mark.parametrize("stage", ["tree", "branch", "pr"])
def test_main_movement_during_publication_preserves_partial_state_and_invalidates_approval(
    saved_repair, monkeypatch, stage
):
    session, config, row, remote = setup(saved_repair, monkeypatch)
    original_event = remote.event

    def event(name):
        original_event(name)
        if name == stage:
            remote.refs["main"] = ref("main", "f" * 40)

    remote.event = event
    result = anyio.run(publish_proposal, session, config, row.id)
    assert result.state == "stale" and result.approved_hash is None
    assert result.last_error == "baseline_stale"
    assert remote.refs["main"]["object"]["sha"] == "f" * 40
    if stage == "pr":
        assert result.outcome["observed_pr_number"] == 41
    else:
        assert "pr" not in remote.events
    with pytest.raises(GitHubMCPError, match="not_authorized"):
        anyio.run(publish_proposal, session, config, row.id)
    session.rollback()


def test_git_api_fixed_paths_create_only_payloads_no_redirect_or_retry(saved_repair):
    session, config, run = saved_repair
    row = prepare_proposal(session, config, run.id)
    p = checked_plan(session, config, row)
    requests = []

    def handler(request):
        requests.append(request)
        return httpx2.Response(201, json={"sha": p.commit_sha}, request=request)

    async def scenario():
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler), follow_redirects=False
        ) as http:
            git = GitObjects(http, p)
            await git.create_branch()
            await git.create_commit()
            with pytest.raises(GitHubMCPError, match="operation_denied"):
                await git.ref("other-branch")
            with pytest.raises(GitHubMCPError, match="operation_denied"):
                await git._request("PATCH", "git/refs/heads/main", {})
            with pytest.raises(GitHubMCPError, match="operation_denied"):
                await git._request(
                    "POST", "git/refs", {"ref": "refs/heads/main", "sha": p.commit_sha}
                )

    anyio.run(scenario)
    assert len(requests) == 2
    assert all(
        str(r.url).startswith(f"https://api.github.com/repos/{p.repository}/git/")
        for r in requests
    )
    assert json.loads(requests[0].content) == {
        "ref": f"refs/heads/{p.head_branch}",
        "sha": p.commit_sha,
    }
    commit = json.loads(requests[1].content)
    assert commit["parents"] == [p.base_sha] and commit["tree"] == p.tree_sha


def test_remote_verifiers_reject_content_parent_or_pr_changes(saved_repair):
    session, config, run = saved_repair
    p = checked_plan(session, config, prepare_proposal(session, config, run.id))
    remote = Remote(p)

    async def objects():
        await remote.create_tree()
        await remote.create_commit()
        await remote.create()

    anyio.run(objects)
    verify_tree(anyio.run(remote.tree), p)
    verify_commit(anyio.run(remote.commit), p)
    rendered = copy.deepcopy(remote.commits[p.commit_sha])
    rendered["message"] = rendered["message"].removesuffix("\n")
    verify_commit(rendered, p)
    verify_pr(remote.prs[0], p)
    damaged = copy.deepcopy(remote.commits[p.commit_sha])
    damaged["parents"] = [{"sha": "0" * 40}]
    with pytest.raises(GitHubMCPError, match="commit_mismatch"):
        verify_commit(damaged, p)
    damaged = copy.deepcopy(remote.trees[p.tree_sha])
    damaged["tree"][0]["mode"] = "100755"
    with pytest.raises(GitHubMCPError, match="tree_mismatch"):
        verify_tree(damaged, p)
    remote.prs[0]["head"]["sha"] = "0" * 40
    with pytest.raises(GitHubMCPError, match="pr_ref_mismatch"):
        verify_pr(remote.prs[0], p)


def test_mcp_pr_only_exact_plan_and_discovery_schema_allowed(saved_repair):
    session, config, run = saved_repair
    p = checked_plan(session, config, prepare_proposal(session, config, run.id))
    sdk = SimpleNamespace(
        list_tools=AsyncMock(
            return_value=SimpleNamespace(
                tools=[
                    SimpleNamespace(name=n, input_schema={"type": "object"})
                    for n in PR_TOOLS
                ],
                next_cursor=None,
            )
        ),
        call_tool=AsyncMock(return_value=CallToolResult(content=[])),
    )

    async def scenario():
        client = ApprovedPRClient(sdk, p)
        await client.discover()
        await client.create()
        args = sdk.call_tool.await_args.args
        assert args[0] == "create_pull_request" and args[1] == client.create_arguments
        for patch in (
            {"head": "main"},
            {"body": "LLM approved"},
            {"repo": "another"},
            {"draft": False},
        ):
            with pytest.raises(GitHubMCPError, match="arguments_denied"):
                await client._call(
                    "create_pull_request", client.create_arguments | patch
                )
        with pytest.raises(GitHubMCPError, match="arguments_denied"):
            await client._call(
                "pull_request_read",
                {**client.scope, "pullNumber": 1, "method": "get_diff"},
            )
        sdk.list_tools.return_value.next_cursor = "more"
        with pytest.raises(GitHubMCPError, match="discovery_denied"):
            await client.discover()

    anyio.run(scenario)
    assert sdk.call_tool.await_count == 1


def test_inspect_pr_support_never_creates_and_unapproved_connect_denied(
    saved_repair, monkeypatch
):
    session, config, run = saved_repair
    p = checked_plan(session, config, prepare_proposal(session, config, run.id))
    remote = Remote(p)

    @asynccontextmanager
    async def connection(*args):
        yield remote

    monkeypatch.setattr("repopilot.github.pr_client._pr_session", connection)
    result = anyio.run(inspect_pr_support, config, p)
    assert result["remote_writes"] == 0 and remote.events == []

    async def denied():
        async with connect_approved_pr(config, p, "0" * 64):
            pytest.fail("unapproved session must not open")

    with pytest.raises(GitHubMCPError, match="not_authorized"):
        anyio.run(denied)


@pytest.mark.parametrize("mode", ["redirect", "timeout", "permission", "oversize"])
def test_git_boundary_bounded_safe_failure_without_retry(saved_repair, mode):
    session, config, run = saved_repair
    p = checked_plan(session, config, prepare_proposal(session, config, run.id))
    calls = []

    def handler(request):
        calls.append(request)
        if mode == "timeout":
            raise httpx2.ReadTimeout("private-token-do-not-expose", request=request)
        if mode == "redirect":
            return httpx2.Response(
                307, headers={"location": "https://attacker.invalid"}, request=request
            )
        if mode == "permission":
            return httpx2.Response(
                403, text="private-token-do-not-expose", request=request
            )
        return httpx2.Response(201, content=b"a" * 1048577, request=request)

    async def scenario():
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler), follow_redirects=False
        ) as http:
            await GitObjects(http, p).create_commit()

    with pytest.raises(GitHubMCPError) as error:
        anyio.run(scenario)
    assert "private-token" not in str(error.value) and len(calls) == 1
