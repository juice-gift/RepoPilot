"""Read back the two owner-approved PRs; test only their bound frozen patches."""

import hashlib
import json
from datetime import UTC, datetime

import anyio

from repopilot.agent.tools import RunScope
from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.models import GitHubPublication, RepositorySnapshot
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.github.client import connect_github_readonly
from repopilot.github.fixture_audit import audit_fixture, embedded_source
from repopilot.github.git_api import _git_session
from repopilot.github.probe import object_payload
from repopilot.github.proposals import checked_plan
from repopilot.github.publication import (
    verify_commit,
    verify_pr,
    verify_ref,
    verify_tree,
)
from repopilot.resolution.patch import Edit, PatchArguments, PatchEngine
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxExecutor, docker
from repopilot.resolution.workspace import Workspace, snapshot_sources

REPO = "juice-gift/repopilot-v5-sandbox"
BASE = "b4279c8b4d862817e6778caa5f87da91d29ed2b7"
IDS = ("ac87b554e57e4a9181116fb36cf66811", "c37153f84a904aa09cb1228f30f7f298")


async def main():
    settings = Settings(github_mcp_allowed_repositories=[REPO])
    assert not settings.github_write_allowed_repositories
    report = {
        "measurement": "actual official MCP/Git API readback and isolated frozen-patch Docker retest",
        "remote_writes": 0,
        "observed_at": datetime.now(UTC).isoformat(),
        "cases": [],
    }
    report["fixture"] = await audit_fixture(
        settings,
        repository=REPO,
        expected_commit=BASE,
        issue_numbers=(1, 2, 3),
        expected_login="juice-gift",
    )
    assert report["fixture"]["status"] == "passed"
    image = docker(
        "image", "inspect", "repopilot-tests:v4", "--format", "{{.Id}}"
    ).strip()
    engine = create_database_engine(settings.database_url)
    try:
        with create_database_session_factory(engine)() as session:
            for identifier in IDS:
                row = session.get(GitHubPublication, identifier)
                plan = checked_plan(session, settings, row)
                assert row.state == "published" and row.approved_hash == row.plan_hash
                async with _git_session(settings, plan) as git:
                    verify_ref(await git.ref("main"), "main", BASE)
                    verify_ref(
                        await git.ref(plan.head_branch),
                        plan.head_branch,
                        plan.commit_sha,
                    )
                    verify_commit(await git.commit(), plan)
                    verify_tree(await git.tree(), plan)
                sources = {}
                async with connect_github_readonly(settings) as reader:
                    for path in plan.files:
                        sources[path] = embedded_source(
                            await reader.file(REPO, path, plan.commit_sha),
                            REPO,
                            plan.commit_sha,
                            path,
                        )
                    payload = object_payload(
                        await reader.pull_request(REPO, row.outcome["pr_number"])
                    )
                    number, url = verify_pr(payload.get("pull_request", payload), plan)
                assert sources == plan.files
                snapshot = session.get(RepositorySnapshot, plan.snapshot_id)
                scope = RunScope(snapshot.repository_id, snapshot.id)
                saved = snapshot_sources(session, scope)
                profile = load_profile(plan.profile)
                profile.require_snapshot({f.path: f.content for f in saved})
                with Workspace(scope, saved) as workspace:
                    root = workspace.root
                    PatchEngine(workspace, profile.editable_paths).apply(
                        PatchArguments(
                            expected_revision=0,
                            edits=[
                                Edit(
                                    path=path,
                                    old_text=workspace.baseline[path],
                                    new_text=sources[path],
                                )
                                for path in plan.changed_paths
                            ],
                        ),
                        attempt=1,
                    )
                    assert workspace.sources() == sources
                    tests = SandboxExecutor(image).run(workspace, profile)
                    assert tests.passed
                assert not root.exists()
                report["cases"].append(
                    {
                        "proposal_id": identifier,
                        "plan_hash": row.plan_hash,
                        "commit_sha": plan.commit_sha,
                        "parent_sha": BASE,
                        "tree_sha": plan.tree_sha,
                        "pr_number": number,
                        "pr_url": url,
                        "draft_open_unmerged_verified": True,
                        "source_sha256": {
                            p: hashlib.sha256(t.encode()).hexdigest()
                            for p, t in sources.items()
                        },
                        "files_equal_approved_plan": True,
                        "tests": tests.model_dump(mode="json"),
                        "workspace_cleaned": True,
                    }
                )
    finally:
        engine.dispose()
    report["sandbox_image"] = image
    report["write_allowlist_empty"] = not Settings().github_write_allowed_repositories
    (REPOSITORY_ROOT / "docs/evaluation/v5-final-live-audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        "Both actual draft PRs, source bytes, baseline and independent Docker retests verified."
    )


if __name__ == "__main__":
    anyio.run(main)
