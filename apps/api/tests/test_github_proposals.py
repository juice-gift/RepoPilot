"""Local approval regression tests. Saved real evidence is test input, not live proof."""

import copy
import json
import os
import subprocess
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from test_github_binding import fixture_data

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.models import (
    GitHubPublication,
    GitHubResolutionRun,
    Repository,
    RepositorySnapshot,
)
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.github.binding import persist_binding
from repopilot.github.client import GitHubMCPError
from repopilot.github.proposals import (
    approve_proposal,
    checked_plan,
    git_object,
    prepare_proposal,
    tree_hash,
)
from repopilot.github.resolution import result_hash
from repopilot.main import create_app


def test_git_objects_match_git(tmp_path):
    content = b"controlled\n"
    path = tmp_path / "source.txt"
    path.write_bytes(content)
    expected = subprocess.run(
        ["git", "hash-object", "--no-filters", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert git_object("blob", content) == expected
    assert tree_hash({}) == "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    with pytest.raises(GitHubMCPError):
        tree_hash({"../x": "no"})


@pytest.fixture
def saved_repair():
    if os.getenv("RUN_DATABASE_TESTS") != "1":
        pytest.skip("requires PostgreSQL")
    audit, sources = fixture_data()
    engine = create_database_engine(Settings().database_url)
    factory = create_database_session_factory(engine)
    config = Settings(
        github_mcp_allowed_repositories=[audit["repository"]],
        github_write_allowed_repositories=[],
    )
    run_id = uuid4().hex
    try:
        with factory() as session:
            bindings = persist_binding(session, audit=audit, sources=sources)
            evidence = json.loads(
                (
                    REPOSITORY_ROOT / "docs/evaluation/v5-bound-qwen-resolution.json"
                ).read_text()
            )["cases"][0]["result"]
            result = copy.deepcopy(evidence)
            snapshot = session.get(RepositorySnapshot, bindings[0].snapshot_id)
            result.update(repository_id=snapshot.repository_id, snapshot_id=snapshot.id)
            run = GitHubResolutionRun(
                id=run_id,
                binding_id=bindings[0].id,
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
                    == f"github://github.com/repositories/{audit['repository_id']}"
                )
            )
            session.commit()
        engine.dispose()


def test_proposal_idempotent_approval_exact_and_tamper_denied(saved_repair):
    session, config, run = saved_repair
    row = prepare_proposal(session, config, run.id)
    assert prepare_proposal(session, config, run.id).id == row.id
    assert row.approved_hash is None and row.state == "awaiting_approval"
    plan = checked_plan(session, config, row)
    assert plan.base_sha == "b4279c8b4d862817e6778caa5f87da91d29ed2b7"
    assert plan.head_branch.startswith("codex/issue-1-") and plan.changed_paths == [
        "fees.py"
    ]
    assert plan.tree_sha == tree_hash(plan.files) and plan.draft
    for digest, text in [
        ("0" * 64, f"APPROVE {row.id}:{row.plan_hash}"),
        (row.plan_hash, "yes"),
    ]:
        with pytest.raises(GitHubMCPError, match="approval_mismatch"):
            approve_proposal(session, config, row.id, digest, text)
        session.rollback()
    approve_proposal(
        session, config, row.id, row.plan_hash, f"APPROVE {row.id}:{row.plan_hash}"
    )
    assert row.approved_hash == row.plan_hash
    payload = copy.deepcopy(row.plan)
    payload["head_branch"] = "main"
    row.plan = payload
    session.flush()
    with pytest.raises(GitHubMCPError, match="integrity"):
        checked_plan(session, config, row)
    session.rollback()


@pytest.mark.parametrize(
    "change",
    ["ambiguous", "untested", "baseline", "source", "result_hash", "patch_hash"],
)
def test_unverified_results_cannot_be_proposed(saved_repair, change):
    session, config, run = saved_repair
    result = copy.deepcopy(run.result)
    if change == "ambiguous":
        result["repair_status"] = "needs_owner_decision"
    elif change == "untested":
        result["test_results"][-1]["revision"] = 0
    elif change == "baseline":
        result["test_results"][0]["workspace_id"] = "other-workspace"
    elif change == "source":
        result["changed_files"][0]["original"] += "bad"
    elif change == "patch_hash":
        result["patch_history"][-1]["after_hashes"]["fees.py"] = "0" * 64
    run.result = result
    run.result_hash = result_hash(result) if change != "result_hash" else "0" * 64
    session.flush()
    with pytest.raises(GitHubMCPError):
        prepare_proposal(session, config, run.id)
    session.rollback()


def test_approval_api_local_origin_and_no_input_override(saved_repair):
    session, config, run = saved_repair
    row = prepare_proposal(session, config, run.id)
    app = create_app(config)
    payload = {
        "expected_hash": row.plan_hash,
        "confirmation": f"APPROVE {row.id}:{row.plan_hash}",
    }
    path = f"/api/github/proposals/{row.id}/approve"
    with TestClient(app, client=("192.0.2.1", 1234)) as remote:
        assert (
            remote.post(
                path, json=payload, headers={"Origin": config.frontend_origin}
            ).status_code
            == 403
        )
    with TestClient(app, client=("127.0.0.1", 1234)) as client:
        assert client.post(path, json=payload).status_code == 403
        headers = {"Origin": config.frontend_origin}
        assert (
            client.post(
                path, json=payload | {"repository": "another/repo"}, headers=headers
            ).status_code
            == 422
        )
        response = client.post(path, json=payload, headers=headers)
        assert response.status_code == 200 and response.json()["approved"] is True
        assert (
            client.post(
                f"/api/github/proposals/{row.id}/revoke", headers=headers
            ).json()["approved"]
            is False
        )
        assert (
            client.post(
                "/api/github/runs",
                headers=headers,
                json={"binding_id": run.binding_id, "issue": "override"},
            ).status_code
            == 422
        )
