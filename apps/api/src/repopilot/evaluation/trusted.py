"""Approved real Python corpus through existing indexing/loop/Docker and V6 grading."""

import json
import platform
import subprocess
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from sqlalchemy import delete

from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.models import Repository
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.evaluation.contracts import CaseResult, Task, digest, file_digest
from repopilot.evaluation.grading import aggregate, resolution_checks
from repopilot.indexing.service import index_snapshot
from repopilot.ingestion.service import ingest_repository
from repopilot.intelligence.service import index_structure
from repopilot.rag.generation import create_agent_provider
from repopilot.rag.tool_calling import AgentTurn, ToolCall
from repopilot.resolution.models import ResolutionRequest
from repopilot.resolution.profiles import TestProfile, load_profile
from repopilot.resolution.runner import run_resolution
from repopilot.resolution.sandbox import SandboxExecutor
from repopilot.resolution.tools import ResolutionLimits, ResolutionTools
from repopilot.resolution.trusted_profiles import read_registry
from repopilot.resolution.workspace import Workspace, snapshot_sources

CORPUS = REPOSITORY_ROOT / "apps/api/evaluation/trusted_python"


class ScriptedPythonProvider:
    """Explicit deterministic workflow coverage, never model-quality evidence."""

    provider_name, model_name = "scripted", "reviewed-python-repairs-v1"

    def __init__(self, profile: TestProfile, *, ambiguous: bool = False):
        path = next(iter(profile.editable_paths))
        if ambiguous:
            self.turns = iter(
                [
                    self.call(
                        "submit_plan",
                        {
                            "expected_revision": 0,
                            "decision": "needs_owner_decision",
                            "summary": "Policy intent requires owner judgment",
                            "steps": ["Request owner policy decision"],
                            "files": [],
                        },
                        1,
                    ),
                    AgentTurn(text="Owner judgment required; no source modified."),
                ]
            )
            return
        start = 3300 if profile.case_id == "trusted-more-itertools" else 1
        old, new = (
            (
                "    windows = windowed(it, window_size)",
                "    windows = windowed(it, window_size, fillvalue=_marker)",
            )
            if profile.case_id == "trusted-more-itertools"
            else (
                "            if age > max_age:",
                "            if age < 0 or age > max_age:",
            )
        )
        self.turns = iter(
            [
                self.call(
                    "read_file",
                    {"path": path, "start_line": start, "end_line": start + 150},
                    1,
                ),
                self.call(
                    "submit_plan",
                    {
                        "expected_revision": 0,
                        "decision": "repair",
                        "summary": "Repair approved historical issue",
                        "steps": ["Reproduce, patch, independently verify"],
                        "files": [path],
                    },
                    2,
                ),
                self.call("run_tests", {"expected_revision": 0}, 3),
                self.call(
                    "apply_patch",
                    {
                        "expected_revision": 0,
                        "edits": [{"path": path, "old_text": old, "new_text": new}],
                    },
                    4,
                ),
                self.call("run_tests", {"expected_revision": 1}, 5),
                AgentTurn(
                    text="Deterministic repair verified; independent human review remains required."
                ),
            ]
        )

    @staticmethod
    def call(name: str, arguments: dict, step: int) -> AgentTurn:
        return AgentTurn(tool_calls=(ToolCall(str(step), name, json.dumps(arguments)),))

    def complete(self, **kwargs) -> AgentTurn:
        return next(self.turns)


def corpus_source(profile: TestProfile) -> dict[str, str]:
    if profile.case_id not in {"trusted-itsdangerous", "trusted-more-itertools"}:
        raise ValueError("Profile is not part of this reviewed real-world corpus")
    root = CORPUS / profile.case_id.removeprefix("trusted-") / "repository"
    result = {}
    for relative in profile.expected_sources:
        path = root / relative
        if not path.resolve().is_relative_to(root.resolve()) or any(
            p.is_symlink() or p.is_junction() for p in (path, *path.parents)
        ):
            raise ValueError("Linked evaluation source is forbidden")
        result[relative] = path.read_text(encoding="utf-8")
    profile.require_snapshot(result)
    return result


def execute_trusted(
    settings: Settings, profile: TestProfile, task: Task, mode: str
) -> CaseResult:
    sources = corpus_source(profile)
    ambiguous = task.expected == "needs_owner_decision"
    provider = (
        ScriptedPythonProvider(profile, ambiguous=ambiguous)
        if mode == "scripted"
        else create_agent_provider(settings)
    )
    executor = SandboxExecutor(profile.image_id, timeout_seconds=40)
    case = {}
    owned_path = None
    with tempfile.TemporaryDirectory(prefix="repopilot-python-eval-") as directory:
        root = Path(directory)
        source_root = root / "repository"
        source_root.mkdir()
        for path, text in sources.items():
            destination = source_root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(text, encoding="utf-8", newline="\n")
        engine = create_database_engine(settings.database_url)
        factory = create_database_session_factory(engine)
        try:
            with factory() as session:
                ingestion = ingest_repository(
                    session,
                    requested_path=str(source_root),
                    allowed_root=root,
                    repository_name="Evaluation-owned approved Python source",
                )
                owned_path = ingestion.repository.local_path
                # These exact bytes are approved projections from the pinned commit.
                ingestion.snapshot.source_revision = profile.commit_sha
                session.commit()
                scope = RunScope(ingestion.repository.id, ingestion.snapshot.id)
                before = snapshot_sources(session, scope)
                embedding = DeterministicEmbeddingProvider()
                index_structure(
                    session,
                    repository_id=scope.repository_id,
                    snapshot_id=scope.snapshot_id,
                )
                index_snapshot(
                    session,
                    repository_id=scope.repository_id,
                    snapshot_id=scope.snapshot_id,
                    provider=embedding,
                )
                with Workspace(scope, before) as workspace:
                    workspace_root = workspace.root
                    tools = ResolutionTools(
                        workspace,
                        profile,
                        executor,
                        ResolutionLimits(),
                        ToolRegistry(
                            session, scope, embedding_factory=lambda: embedding
                        ),
                    )
                    result = run_resolution(
                        ResolutionRequest(
                            repository_id=scope.repository_id,
                            snapshot_id=scope.snapshot_id,
                            profile=profile.case_id,
                            issue=task.question or profile.bound_issue,
                        ),
                        tools=tools,
                        provider=provider,
                    )
                    independent = (
                        executor.run(workspace, profile) if not ambiguous else None
                    )
                result.workspace_cleaned = not workspace_root.exists()
                case = {
                    "result": result.model_dump(mode="json"),
                    "original_unchanged": corpus_source(profile) == sources,
                    "snapshot_unchanged": snapshot_sources(session, scope) == before,
                    "profile_hash": profile.fingerprint(),
                    "commit_sha": profile.commit_sha,
                    "execution_limits": asdict(ResolutionLimits()),
                    "input_kind": "original Issue body"
                    if not ambiguous
                    else "explicit ambiguity task",
                }
                if independent is not None:
                    case["independent_final_test"] = independent.model_dump(mode="json")
        finally:
            try:
                if owned_path:
                    with factory() as session:
                        session.execute(
                            delete(Repository).where(
                                Repository.local_path == owned_path
                            )
                        )
                        session.commit()
                        if (
                            session.query(Repository)
                            .filter_by(local_path=owned_path)
                            .first()
                            is not None
                        ):
                            raise ValueError("Evaluation-owned database cleanup failed")
            finally:
                engine.dispose()
    case["evaluation_inputs_cleaned"] = not source_root.exists()
    return resolution_checks(task, case, approved_profile=profile)


def run_trusted(settings: Settings, *, mode: str, output: Path) -> dict:
    from repopilot.evaluation.harness import failure_result, save_report

    if mode not in {"scripted", "live"} or (
        mode == "live" and settings.generation_provider == "deterministic"
    ):
        raise ValueError("Invalid trusted evaluation mode/provider")
    registry = read_registry(
        settings.trusted_profile_registry, settings.trusted_profile_registry_sha256
    )
    ids = {p.id for p in registry.profiles}
    if not {"trusted-itsdangerous", "trusted-more-itertools"} <= ids:
        raise ValueError("Both approved corpus profiles are required")
    tasks = [
        Task(
            id="python/" + name,
            category="resolution",
            source_id=name,
            expected="verified_repair",
            legacy_id="trusted-" + name,
        )
        for name in ("itsdangerous", "more-itertools")
    ]
    tasks.append(
        Task(
            id="python/ambiguous-clock-drift",
            category="resolution",
            source_id="itsdangerous",
            expected="needs_owner_decision",
            legacy_id="trusted-itsdangerous",
            question="A caller requests clock drift tolerance but has supplied no allowed tolerance, compatibility policy, or timestamp interval. Determine intent; do not assume a policy or modify source until the owner decides.",
        )
    )

    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=REPOSITORY_ROOT, text=True, timeout=10
        ).strip()

    report = {
        "schema_version": 1,
        "definitions": "pre-v8-trusted-evidence-1",
        "review_policy": "unreviewed",
        "dataset": {
            "name": "approved-real-python",
            "version": 1,
            "hash": digest(
                {
                    "registry": settings.trusted_profile_registry_sha256,
                    "tasks": [t.model_dump() for t in tasks],
                }
            ),
            "total_tasks": len(tasks),
        },
        "selection": [t.id for t in tasks],
        "mode": mode,
        "measurement": "Actual configured model with real Docker"
        if mode == "live"
        else "Scripted decisions with real Docker; not LLM-quality evidence",
        "code_commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "started_at": datetime.now(UTC).isoformat(),
        "complete": False,
        "runtime": {
            "model": (
                settings.qwen_generation_model
                if settings.generation_provider == "qwen"
                else settings.generation_model
            )
            if mode == "live"
            else ScriptedPythonProvider.model_name,
            "provider": settings.generation_provider if mode == "live" else "scripted",
            "python": platform.python_version(),
            "max_output_tokens": settings.generation_max_output_tokens,
            "endpoint_hash": digest(settings.dashscope_base_url)
            if mode == "live" and settings.generation_provider == "qwen"
            else None,
            "embedding": "deterministic-token-hash/512",
            "policy_sha256": settings.trusted_profile_registry_sha256,
            "fingerprints": {
                name: file_digest(REPOSITORY_ROOT / "apps/api/src/repopilot" / name)
                for name in (
                    "evaluation/trusted.py",
                    "evaluation/harness.py",
                    "evaluation/grading.py",
                    "resolution/runner.py",
                    "resolution/sandbox.py",
                    "resolution/profiles.py",
                    "resolution/trusted_profiles.py",
                    "rag/generation.py",
                )
            },
        },
        "limitations": [
            "Two small historical issues do not establish general repair accuracy.",
            "Current provider contracts expose no trustworthy usage/cost; null is unavailable, not zero.",
            "Protected tests are reviewed local tests, not the complete upstream suites.",
            "Earlier task-summary Qwen failures remain separate evidence; this corpus uses original Issue bodies.",
            "No GitHub writes; temporary source/Snapshot records are evaluation-owned and cleaned.",
        ],
        "cases": [],
        "aggregate": aggregate([]),
    }
    results = []
    save_report(report, output)
    for task in tasks:
        started = perf_counter()
        try:
            profile = load_profile(
                task.legacy_id,
                registry_path=settings.trusted_profile_registry,
                registry_digest=settings.trusted_profile_registry_sha256,
            )
            case = execute_trusted(settings, profile, task, mode)
        except Exception as error:  # noqa: BLE001 - checkpoint sanitized per-case failures, never exception text
            case = failure_result(task, error)
        case.latency_ms = round((perf_counter() - started) * 1000, 3)
        results.append(case)
        report.update(
            cases=[c.model_dump() for c in results], aggregate=aggregate(results)
        )
        save_report(report, output)
        print(f"{task.id}: {case.status}", flush=True)
    report.update(complete=True, finished_at=datetime.now(UTC).isoformat())
    save_report(report, output)
    return report
