"""Nested publication fault injection using saved real Docker evidence, no live writes."""

import copy
import hashlib
import json
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import anyio
import pytest
from sqlalchemy import delete
from test_github_publication import Remote

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.models import GitHubPublication, GitHubResolutionRun, Repository
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.github.binding import persist_binding
from repopilot.github.client import GitHubMCPError
from repopilot.github.git_api import GitObjects, require_write_scope
from repopilot.github.proposals import approve_proposal, checked_plan, prepare_proposal
from repopilot.github.publication import (
    publish_proposal,
    verify_repository,
    verify_tree,
)
from repopilot.github.resolution import result_hash
from repopilot.github.trees import nested_tree, replace_blobs
from repopilot.resolution.profiles import load_profile


def recursive_tree(plan):
    blobs = replace_blobs(plan.baseline_entries, plan.files)
    entries = [
        {"path": path, "mode": value["mode"], "sha": value["sha"], "type": "blob"}
        for path, value in blobs.items()
    ]
    directories = {
        "/".join(path.split("/")[:i])
        for path in blobs
        for i in range(1, len(path.split("/")))
    }
    for path in directories:
        prefix = path + "/"
        entries.append(
            {
                "path": path,
                "mode": "040000",
                "type": "tree",
                "sha": nested_tree(
                    {
                        p[len(prefix) :]: v
                        for p, v in blobs.items()
                        if p.startswith(prefix)
                    }
                ),
            }
        )
    return {"sha": plan.tree_sha, "truncated": False, "tree": entries}


@pytest.fixture
def saved_trusted():
    if os.getenv("RUN_DATABASE_TESTS") != "1":
        pytest.skip("requires migrated PostgreSQL")
    root = REPOSITORY_ROOT / "apps/api/evaluation/trusted_python"
    registry = root / "profiles.json"
    config = Settings(
        trusted_profile_registry=registry,
        trusted_profile_registry_sha256=hashlib.sha256(
            registry.read_bytes()
        ).hexdigest(),
        github_mcp_allowed_repositories=["pallets/itsdangerous"],
        github_write_allowed_repositories=[],
    )
    profile = load_profile(
        "trusted-itsdangerous",
        registry_path=registry,
        registry_digest=config.trusted_profile_registry_sha256,
    )
    sources = {
        p: (root / "itsdangerous/repository" / p).read_text(encoding="utf-8")
        for p in profile.expected_sources
    }
    remote_id = int(uuid4().hex[:12], 16)
    audit = {
        "status": "passed",
        "checks": {"simulated_remote": True},
        "repository_id": remote_id,
        "repository": profile.repository,
        "actual_commit": profile.commit_sha,
        "issues": [
            {
                "case": profile.case_id,
                "number": profile.issue_number,
                "matches_frozen_contract": True,
            }
        ],
    }
    engine = create_database_engine(config.database_url)
    factory = create_database_session_factory(engine)
    run_id = uuid4().hex
    try:
        with factory() as session:
            binding = persist_binding(
                session, audit=audit, sources=sources, approved_profiles=[profile]
            )[0]
            raw = json.loads(
                (
                    REPOSITORY_ROOT / "docs/evaluation/pre-v8-bound-proposals.json"
                ).read_text(encoding="utf-8")
            )["cases"][0]["result"]
            result = copy.deepcopy(raw)
            from repopilot.db.models import RepositorySnapshot

            snapshot = session.get(RepositorySnapshot, binding.snapshot_id)
            result.update(repository_id=snapshot.repository_id, snapshot_id=snapshot.id)
            run = GitHubResolutionRun(
                id=run_id,
                binding_id=binding.id,
                state="completed",
                result=result,
                result_hash=result_hash(result),
            )
            session.add(run)
            session.commit()
            yield session, config, run
    finally:
        with factory() as session:
            session.execute(
                delete(GitHubPublication).where(GitHubPublication.run_id == run_id)
            )
            session.execute(
                delete(GitHubResolutionRun).where(GitHubResolutionRun.id == run_id)
            )
            session.execute(
                delete(Repository).where(
                    Repository.local_path
                    == f"github://github.com/repositories/{remote_id}"
                )
            )
            session.commit()
        engine.dispose()


@pytest.mark.parametrize("failure", [None, "tree", "commit", "branch", "pr"])
def test_nested_publication_reconciles_without_duplicate_remote_effects(
    saved_trusted, monkeypatch, failure
):
    session, config, run = saved_trusted
    row = prepare_proposal(session, config, run.id)
    approve_proposal(
        session, config, row.id, row.plan_hash, f"APPROVE {row.id}:{row.plan_hash}"
    )
    plan = checked_plan(session, config, row)

    class NestedRemote(Remote):
        async def create_tree(self):
            tree = recursive_tree(self.p)
            self.trees[self.p.tree_sha] = tree
            self.event("tree")
            return tree

    remote = NestedRemote(plan, failure)
    config.github_write_allowed_repositories = config.github_mcp_allowed_repositories

    @asynccontextmanager
    async def connection(settings, proposal, digest):
        require_write_scope(settings, proposal, digest)
        yield remote

    async def preflight(*args):
        return {"measurement": "fake private target, no actual GitHub writes"}

    monkeypatch.setattr("repopilot.github.publication.connect_git_objects", connection)
    monkeypatch.setattr("repopilot.github.publication.connect_approved_pr", connection)
    monkeypatch.setattr("repopilot.github.publication.readonly_preflight", preflight)
    first = anyio.run(publish_proposal, session, config, row.id)
    if failure:
        assert first.state == "retry_needed"
        first = anyio.run(publish_proposal, session, config, row.id)
    assert first.state == "published" and first.outcome["exact_content_verified"]
    anyio.run(publish_proposal, session, config, row.id)
    assert remote.events == ["tree", "commit", "branch", "pr"]
    payload = GitObjects(None, plan).write_payloads["git/trees"]
    assert payload["base_tree"] == plan.baseline_tree_sha
    assert len(payload["tree"]) == len(plan.changed_paths)
    assert (
        payload["tree"][0]["mode"]
        == plan.baseline_entries[plan.changed_paths[0]]["mode"]
    )
    with pytest.raises(GitHubMCPError):
        verify_repository({**remote.metadata_value, "private": False}, plan)
    tree = recursive_tree(plan)
    verify_tree(tree, plan)
    tree["tree"].append(copy.deepcopy(tree["tree"][0]))
    with pytest.raises(GitHubMCPError, match="remote_tree_mismatch"):
        verify_tree(tree, plan)
