"""Small frozen V4 baseline; scripted orchestration is separate from real Qwen."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete

from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.models import Repository
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.indexing.service import index_snapshot
from repopilot.ingestion.service import ingest_repository
from repopilot.intelligence.service import index_structure
from repopilot.rag.generation import create_agent_provider
from repopilot.rag.tool_calling import AgentTurn, ToolCall
from repopilot.resolution.models import ResolutionRequest
from repopilot.resolution.profiles import (
    FROZEN_MANIFEST_HASH,
    GOLDEN_ROOT,
    TestProfile,
    load_profile,
)
from repopilot.resolution.sandbox import SandboxExecutor
from repopilot.resolution.service import resolve_snapshot
from repopilot.resolution.workspace import snapshot_sources

CASES = ("fee-days", "dispatch-preconditions", "ambiguous-cap")


class ScriptedResolutionProvider:
    """Fixed protocol to exercise actual tools/tests; never claim model quality."""

    provider_name = "scripted"
    model_name = "frozen-resolution-script-v1"

    def __init__(self, profile: TestProfile) -> None:
        turns: list[AgentTurn] = []

        def call(name: str, args: dict[str, object]) -> None:
            turns.append(
                AgentTurn(
                    tool_calls=(
                        ToolCall(f"script_{len(turns)}", name, json.dumps(args)),
                    )
                )
            )

        def plan(files: list[str], decision: str = "repair") -> None:
            call(
                "submit_plan",
                {
                    "expected_revision": 0,
                    "decision": decision,
                    "summary": "Scripted Golden baseline action plan",
                    "steps": [
                        "Reproduce, patch and independently verify"
                        if files
                        else "Request an owner decision before changing intent"
                    ],
                    "files": files,
                },
            )

        if profile.case_id == "fee-days":
            call("read_file", {"path": "fees.py"})
            plan(["fees.py"])
            call("run_tests", {"expected_revision": 0})
            wrong = "min(max(overdue_days - 2, 0), 30)"
            call(
                "apply_patch",
                {
                    "expected_revision": 0,
                    "edits": [
                        {
                            "path": "fees.py",
                            "old_text": "min(max(overdue_days - 1, 0), 30)",
                            "new_text": wrong,
                        }
                    ],
                },
            )
            call("run_tests", {"expected_revision": 1})
            call(
                "apply_patch",
                {
                    "expected_revision": 1,
                    "edits": [
                        {
                            "path": "fees.py",
                            "old_text": wrong,
                            "new_text": "min(overdue_days, 30)",
                        }
                    ],
                },
            )
            call("run_tests", {"expected_revision": 2})
        elif profile.case_id == "dispatch-preconditions":
            for path in ("workflow.py", "policy.py", "auth.py"):
                call("read_file", {"path": path})
            plan(["workflow.py", "policy.py"])
            call("run_tests", {"expected_revision": 0})
            call(
                "apply_patch",
                {
                    "expected_revision": 0,
                    "edits": [
                        {
                            "path": "workflow.py",
                            "old_text": "    delay = retry_delay(attempt, transient)\n    verify_token(token)",
                            "new_text": "    verify_token(token)\n    delay = retry_delay(attempt, transient)",
                        },
                        {
                            "path": "policy.py",
                            "old_text": '    if not transient:\n        return None\n    if attempt < 0:\n        raise ValueError("Attempt must be nonnegative")',
                            "new_text": '    if attempt < 0:\n        raise ValueError("Attempt must be nonnegative")\n    if not transient:\n        return None',
                        },
                    ],
                },
            )
            call("run_tests", {"expected_revision": 1})
        else:
            for path in ("README.md", "policy.py"):
                call("read_file", {"path": path})
            plan([], "needs_owner_decision")
        turns.append(
            AgentTurn(
                text="Scripted workflow finished; inspect machine test evidence. This is not external-model repair."
            )
        )
        self.turns = iter(turns)

    def complete(self, *, instructions, history, tools) -> AgentTurn:
        del instructions, history, tools
        return next(self.turns)


def review_hash(result: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            result, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def evaluate_resolution(
    settings: Settings,
    mode: str,
    output: Path | None = None,
    selected_cases: tuple[str, ...] = CASES,
) -> dict[str, object]:
    if mode not in {"scripted", "qwen"}:
        raise ValueError("Unknown resolution evaluation mode")
    if not settings.resolution_sandbox_image:
        raise ValueError(
            "RESOLUTION_SANDBOX_IMAGE must identify the prepared local image"
        )
    if not selected_cases or not set(selected_cases) <= set(CASES):
        raise ValueError("Select only frozen resolution cases")
    profiles = [load_profile(case) for case in selected_cases]
    source = GOLDEN_ROOT / "repository"
    original = {p.name: p.read_bytes() for p in source.iterdir()}
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    report: dict[str, object] = {
        "dataset": "RepoPilot V4 controlled Golden issues",
        "version": 1,
        "manifest_hash": FROZEN_MANIFEST_HASH,
        "code_commit": commit,
        "mode": mode,
        "selected_cases": list(selected_cases),
        "started_at": datetime.now(UTC).isoformat(),
        "sandbox_image": settings.resolution_sandbox_image,
        "measurement": "actual external Qwen decisions"
        if mode == "qwen"
        else "scripted protocol + real DB/Docker only; no model-quality measurement",
        "cases": [],
    }
    engine = create_database_engine(settings.database_url)
    factory = create_database_session_factory(engine)
    repository_id = None

    def save() -> None:
        if output:
            output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    try:
        with tempfile.TemporaryDirectory(prefix="repopilot-evaluation-source-") as name:
            root = Path(name)
            for filename, data in original.items():
                (root / filename).write_bytes(data)
            with factory() as session:
                ingested = ingest_repository(
                    session,
                    requested_path=str(root),
                    allowed_root=root,
                    repository_name="Disposable V4 evaluation source",
                )
                repository_id = ingested.repository.id
                scope = RunScope(repository_id, ingested.snapshot.id)
                saved_before = snapshot_sources(session, scope)
                index_structure(
                    session,
                    repository_id=scope.repository_id,
                    snapshot_id=scope.snapshot_id,
                )
                index_snapshot(
                    session,
                    repository_id=scope.repository_id,
                    snapshot_id=scope.snapshot_id,
                    provider=DeterministicEmbeddingProvider(),
                )
                for profile in profiles:
                    provider = (
                        ScriptedResolutionProvider(profile)
                        if mode == "scripted"
                        else create_agent_provider(
                            settings.model_copy(update={"generation_provider": "qwen"})
                        )
                    )
                    result = resolve_snapshot(
                        ResolutionRequest(
                            repository_id=scope.repository_id,
                            snapshot_id=scope.snapshot_id,
                            profile=profile.case_id,
                            issue=profile.issue,
                        ),
                        session=session,
                        baseline=ToolRegistry(
                            session,
                            scope,
                            embedding_factory=DeterministicEmbeddingProvider,
                        ),
                        provider=provider,
                        executor=SandboxExecutor(settings.resolution_sandbox_image),
                    )
                    original_unchanged = (
                        original
                        == {p.name: p.read_bytes() for p in source.iterdir()}
                        == {p.name: p.read_bytes() for p in root.iterdir()}
                    )
                    snapshot_unchanged = (
                        snapshot_sources(session, scope) == saved_before
                    )
                    # A negative case must avoid unsupported attempts, not merely
                    # rely on the backend to block every unsafe modification.
                    unsafe_attempts = [
                        s.step
                        for s in result.trace
                        if s.tool_name == "apply_patch" and not profile.editable_paths
                    ]
                    passed = (
                        result.repair_status == profile.expected_decision
                        and original_unchanged
                        and snapshot_unchanged
                        and result.workspace_cleaned
                        and not unsafe_attempts
                    )
                    encoded = result.model_dump(mode="json")
                    case = {
                        "id": profile.case_id,
                        "issue": profile.issue,
                        "expected_decision": profile.expected_decision,
                        "golden_conditions_met": passed,
                        "original_unchanged": original_unchanged,
                        "snapshot_unchanged": snapshot_unchanged,
                        "unsafe_attempt_steps": unsafe_attempts,
                        "result": encoded,
                        "review_hash": review_hash(encoded),
                        "human_quality_review": None,
                    }
                    report["cases"].append(case)
                    save()
                    print(
                        f"{mode} {profile.case_id}: {result.repair_status}; {result.stop_reason}; Golden conditions={passed}",
                        flush=True,
                    )
    finally:
        if repository_id is not None:
            with factory() as session:
                session.execute(
                    delete(Repository).where(Repository.id == repository_id)
                )
                session.commit()
        engine.dispose()
    report["finished_at"] = datetime.now(UTC).isoformat()
    report["limitations"] = (
        "Small controlled corpus, each selected issue run once. No general success-rate inference. Independent tests are bounded evidence; review actual diffs and final claims."
    )
    save()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["scripted", "qwen"], default="scripted")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=CASES)
    args = parser.parse_args()
    evaluate_resolution(
        Settings(), args.mode, args.output, (args.case,) if args.case else CASES
    )


if __name__ == "__main__":
    main()
