"""Narrow adapters for existing pipelines, with evaluation-owned source/DB cleanup."""

import re
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import delete

from repopilot.config import Settings
from repopilot.db.models import Repository
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.evaluation.agent import evaluate_agent
from repopilot.evaluation.contracts import CaseResult, Task
from repopilot.evaluation.grading import resolution_checks
from repopilot.evaluation.resolution import evaluate_resolution
from repopilot.evaluation.runner import DEFAULT_EVALUATION_ROOT, evaluate_retrieval
from repopilot.evaluation.structural import evaluate_structure
from repopilot.indexing.service import index_snapshot
from repopilot.ingestion.service import ingest_repository
from repopilot.rag.generation import create_generation_provider
from repopilot.rag.service import answer_repository_question


@contextmanager
def owned_inputs(settings: Settings):
    with tempfile.TemporaryDirectory(prefix="repopilot-v6-") as name:
        root = Path(name)
        # Do not include generated Python caches in frozen inputs.
        shutil.copytree(
            DEFAULT_EVALUATION_ROOT,
            root,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        paths = [
            str((root / d).resolve())
            for d in ("golden_repository", "structural_golden", "agent_golden")
        ]
        engine = create_database_engine(settings.database_url)
        try:
            yield root
        finally:
            try:
                with create_database_session_factory(engine)() as session:
                    session.execute(
                        delete(Repository).where(Repository.local_path.in_(paths))
                    )
                    session.commit()
            finally:
                engine.dispose()


class ScriptedRagProvider:
    provider_name = "scripted"
    model_name = "v6-grounding-protocol-v1"

    def generate(self, *, instructions: str, input_text: str) -> str:
        del instructions
        # Exercise generation and citation resolution; contains no reference answer.
        ids = re.findall(r"BEGIN UNTRUSTED REPOSITORY EVIDENCE (E\d+)", input_text)
        return "Inspect the supplied source for this question. " + (
            f"[{ids[0]}]" if ids else "[E999]"
        )


def rag_case(settings: Settings, root: Path, task: Task, mode: str) -> dict:
    engine = create_database_engine(settings.database_url)
    embedding = DeterministicEmbeddingProvider()
    try:
        with create_database_session_factory(engine)() as session:
            ingestion = ingest_repository(
                session,
                requested_path=str(root / "golden_repository"),
                allowed_root=root,
                repository_name="V6 owned RAG",
            )
            rid, sid = ingestion.repository.id, ingestion.snapshot.id
            index_snapshot(
                session, repository_id=rid, snapshot_id=sid, provider=embedding
            )
            result = answer_repository_question(
                session,
                repository_id=rid,
                snapshot_id=sid,
                question=task.question,
                top_k=5,
                context_character_limit=12000,
                context_max_evidence=5,
                embedding_provider=embedding,
                generation_provider=(
                    ScriptedRagProvider()
                    if mode == "scripted"
                    else create_generation_provider(
                        settings.model_copy(update={"generation_provider": "qwen"})
                    )
                ),
            )
            return {
                "answer": result.answer,
                "citations": [asdict(c) for c in result.citations.citations],
                "invalid_ids": list(result.citations.invalid_evidence_ids),
                "retrieved": [asdict(e) for e in result.retrieval.evidence],
                "generation_model": result.generation_model,
                "claim_check": task.claim_check,
            }
    finally:
        engine.dispose()


def citation_identity(sources: list[dict], root: Path) -> bool:
    if not sources:
        return False
    for source in sources:
        path = (root / source["file_path"]).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            return False
        start, end = source.get("start_line"), source.get("end_line")
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or start < 1
            or end < start
        ):
            return False
        expected = "\n".join(
            path.read_text(encoding="utf-8").splitlines()[start - 1 : end]
        )
        if not source.get("content") or source["content"].strip() != expected.strip():
            return False
    return True


def execute(
    task: Task, settings: Settings, mode: str, strategy: str, root: Path
) -> CaseResult:
    if task.category == "resolution":
        report = evaluate_resolution(
            settings,
            "qwen" if mode == "live" else "scripted",
            selected_cases=(task.legacy_id,),
        )
        return resolution_checks(task, report["cases"][0])
    if task.category == "retrieval":
        report = evaluate_retrieval(
            database_url=settings.database_url,
            repository_path=root / "golden_repository",
            dataset_path=root / "dataset.json",
            strategy=strategy,
            selected_cases=(task.legacy_id,),
        )
        case = report["cases"][0]
        found = case["first_relevant_rank"] is not None
        return CaseResult(
            id=task.id,
            category=task.category,
            status="passed" if found else "failed",
            checks={"evidence_discovery": "passed" if found else "failed"},
            evidence=report,
            failures=[] if found else ["retrieval_failure"],
        )
    if task.category == "structure":
        report = evaluate_structure(settings.database_url, root)
        passed = not any(report["bad_cases"].values())
        return CaseResult(
            id=task.id,
            category=task.category,
            status="passed" if passed else "failed",
            evidence=report,
            failures=[] if passed else ["missing_or_irrelevant_evidence"],
        )
    if task.category == "investigation":
        report = evaluate_agent(
            settings=settings,
            mode="qwen" if mode == "live" else "scripted",
            root=root,
            selected_cases=(task.legacy_id,),
        )
        case = report["cases"][0]
        valid = bool(case["citation_ids"]) and not case["invalid_citation_ids"]
        sources = [
            s
            for s in case["result"]["sources"]
            if s["evidence_id"] in case["citation_ids"]
        ]
        identity = citation_identity(sources, root / "agent_golden")
        found = case["expected_evidence_found"]
        failures = [] if found else ["missing_or_irrelevant_evidence"]
        if not valid or not identity:
            failures.append("unsupported_citation")
        stop = case["stop_reason"]
        status = "unverified"
        if stop == "provider_failure":
            status = "provider_error"
            failures.append("provider_failure")
        elif stop != "completed":
            status = "failed"
            failures.append("agent_limit_exhaustion")
        elif failures:
            status = "failed"
        return CaseResult(
            id=task.id,
            category=task.category,
            status=status,
            checks={
                "evidence_discovery": "passed" if found else "failed",
                "citation_validity": "passed" if valid else "failed",
                "citation_identity": "passed" if identity else "failed",
                "claim_support": "unverified",
            },
            evidence=case,
            failures=failures,
            tool_calls=case["step_count"],
            model_turns=case["model_calls"],
        )
    case = rag_case(settings, root, task, mode)
    found = all(
        any(
            s["file_path"] == e["file_path"] and s["symbol_name"] == e["symbol_name"]
            for s in case["retrieved"]
        )
        for e in task.evidence
    )
    valid = bool(case["citations"]) and not case["invalid_ids"]
    identity = citation_identity(case["citations"], root / "golden_repository")
    failures = ([] if found else ["retrieval_failure"]) + (
        [] if valid and identity else ["unsupported_citation"]
    )
    return CaseResult(
        id=task.id,
        category=task.category,
        status="failed" if failures else "unverified",
        checks={
            "evidence_discovery": "passed" if found else "failed",
            "citation_validity": "passed" if valid else "failed",
            "citation_identity": "passed" if identity else "failed",
            "claim_support": "unverified",
        },
        evidence=case,
        failures=failures,
        model_turns=1,
    )
