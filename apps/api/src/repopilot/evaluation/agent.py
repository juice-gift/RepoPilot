"""Small frozen investigation baseline, not a general agent accuracy benchmark."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from repopilot.agent.models import AgentRequest, AgentResult
from repopilot.agent.runner import AGENT_INSTRUCTIONS, run_investigation
from repopilot.agent.tools import RunScope, ToolRegistry
from repopilot.config import Settings
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.evaluation.runner import DEFAULT_EVALUATION_ROOT
from repopilot.indexing.service import index_snapshot
from repopilot.ingestion.service import ingest_repository
from repopilot.intelligence.navigation import search_symbols
from repopilot.intelligence.service import index_structure
from repopilot.rag.generation import create_agent_provider
from repopilot.rag.tool_calling import AgentProvider, AgentTurn, ToolCall


class ScriptCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    arguments: dict[str, object]


class InvestigationTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    task: str
    expected_files: list[str]
    expected_symbols: list[str]
    required_source_fragments: list[str]
    expected_conclusion: str
    script: list[ScriptCall]
    scripted_answer: str


class InvestigationDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    tasks: list[InvestigationTask]


def load_agent_dataset(root: Path = DEFAULT_EVALUATION_ROOT) -> InvestigationDataset:
    manifest = json.loads((root / "agent_manifest.json").read_text(encoding="utf-8"))
    if "agent_dataset.json" not in manifest:
        raise ValueError("Frozen dataset is missing from the manifest")
    for relative, expected_hash in manifest.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Agent manifest path escapes evaluation directory")
        actual = hashlib.sha256(
            path.read_text(encoding="utf-8").replace("\r\n", "\n").encode()
        ).hexdigest()
        if actual != expected_hash:
            raise ValueError(f"Frozen agent input changed: {relative}")
    actual_files = {
        p.relative_to(root).as_posix()
        for p in (root / "agent_golden").rglob("*")
        if p.is_file()
    }
    if actual_files != {p for p in manifest if p.startswith("agent_golden/")}:
        raise ValueError("Agent corpus file set changed")
    dataset = InvestigationDataset.model_validate_json(
        (root / "agent_dataset.json").read_text(encoding="utf-8")
    )
    if len({task.id for task in dataset.tasks}) != len(dataset.tasks):
        raise ValueError("Duplicate investigation task IDs")
    return dataset


class BaselineScriptProvider:
    """Replay declared calls; verifies orchestration only, not LLM decision quality."""

    provider_name = "scripted"
    model_name = "frozen-investigation-script-v1"

    def __init__(self, task: InvestigationTask) -> None:
        self.task = task

    def complete(
        self,
        *,
        instructions: str,
        history: list[dict[str, object]],
        tools: list[dict[str, object]],
    ) -> AgentTurn:
        del instructions, tools
        completed = sum(h.get("type") == "function_call_output" for h in history)
        if completed < len(self.task.script):
            call = self.task.script[completed]
            return AgentTurn(
                tool_calls=(
                    ToolCall(
                        f"baseline_{completed}", call.name, json.dumps(call.arguments)
                    ),
                )
            )
        return AgentTurn(text=self.task.scripted_answer)


def summarize_task(
    session: Session, task: InvestigationTask, result: AgentResult
) -> dict[str, object]:
    read_sources = [
        s for s in result.sources if s.content is not None and not s.truncated
    ]
    found_files = sorted({s.file_path for s in read_sources})
    definitions = search_symbols(
        session, result.repository_id, result.snapshot_id, limit=500
    )
    found_symbols = sorted(
        {
            symbol.qualified_name
            for symbol in definitions
            if any(
                source.file_path == symbol.file_path
                and source.start_line is not None
                and source.end_line is not None
                and source.start_line <= symbol.start_line
                and source.end_line >= symbol.end_line
                for source in read_sources
            )
        }
    )
    combined_source = "\n".join(s.content or "" for s in read_sources)
    missing_files = sorted(set(task.expected_files) - set(found_files))
    missing_symbols = sorted(set(task.expected_symbols) - set(found_symbols))
    missing_fragments = [
        fragment
        for fragment in task.required_source_fragments
        if fragment not in combined_source
    ]
    citations = sorted(set(re.findall(r"\[(E\d+_\d+)\]", result.final_answer)))
    review_payload = {
        "final_answer": result.final_answer,
        "sources": [
            s.model_dump(
                include={
                    "evidence_id",
                    "file_path",
                    "start_line",
                    "end_line",
                    "content",
                    "truncated",
                }
            )
            for s in result.sources
        ],
    }
    review_hash = hashlib.sha256(
        json.dumps(review_payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    return {
        "id": task.id,
        "task": task.task,
        "expected_files": task.expected_files,
        "expected_symbols": task.expected_symbols,
        "expected_conclusion": task.expected_conclusion,
        "actual_tools": [step.tool_name for step in result.trace],
        "step_count": result.total_steps,
        "model_calls": result.diagnostics.model_calls,
        "stop_reason": result.stop_reason,
        "found_files": found_files,
        "found_symbols": found_symbols,
        "missing_files": missing_files,
        "missing_symbols": missing_symbols,
        "missing_source_fragments": missing_fragments,
        "expected_evidence_found": not (
            missing_files or missing_symbols or missing_fragments
        ),
        "multistep": result.total_steps >= 2,
        "citation_ids": citations,
        "invalid_citation_ids": result.diagnostics.invalid_evidence_ids,
        "grounded_final_answer": None,
        "grounding_review": "Requires manual comparison of final claims against the saved trace/source; citation validity alone is not grounding.",
        "review_hash": review_hash,
        "result": result.model_dump(mode="json"),
    }


def evaluate_agent(
    *, settings: Settings, mode: str = "scripted", root: Path = DEFAULT_EVALUATION_ROOT
) -> dict[str, object]:
    if mode not in ("scripted", "qwen", "openai"):
        raise ValueError("Unknown evaluation mode")
    dataset = load_agent_dataset(root)
    engine = create_database_engine(settings.database_url)
    factory = create_database_session_factory(engine)
    cases: list[dict[str, object]] = []
    try:
        with factory() as session:
            ingestion = ingest_repository(
                session,
                requested_path=str(root / "agent_golden"),
                allowed_root=root,
                repository_name="RepoPilot V3 Investigation Golden Repository",
            )
            scope = RunScope(ingestion.repository.id, ingestion.snapshot.id)
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
            for task in dataset.tasks:
                provider: AgentProvider = (
                    BaselineScriptProvider(task)
                    if mode == "scripted"
                    else create_agent_provider(
                        settings.model_copy(update={"generation_provider": mode})
                    )
                )
                registry = ToolRegistry(
                    session, scope, embedding_factory=DeterministicEmbeddingProvider
                )
                result = run_investigation(
                    AgentRequest(
                        repository_id=scope.repository_id,
                        snapshot_id=scope.snapshot_id,
                        question=task.task,
                    ),
                    registry=registry,
                    provider=provider,
                )
                cases.append(summarize_task(session, task, result))
            return {
                "dataset_version": dataset.version,
                "mode": mode,
                "embedding_provider": "deterministic-token-hash (pipeline baseline only)",
                "snapshot_hash": ingestion.snapshot.content_hash,
                "instructions_sha256": hashlib.sha256(
                    AGENT_INSTRUCTIONS.encode()
                ).hexdigest(),
                "limitations": "Three small controlled tasks. Scripted calls do not measure model decisions. Manual grounding review is separate; no general accuracy claim.",
                "task_count": len(cases),
                "cases": cases,
            }
    finally:
        engine.dispose()


def apply_grounding_reviews(
    report: dict[str, object], reviews: dict[str, dict[str, object]]
) -> None:
    for case in report["cases"]:
        review = reviews.get(case["id"])
        if review is None or review.get("review_hash") != case["review_hash"]:
            raise ValueError(
                "Grounding review does not match this exact answer and evidence"
            )
        if not isinstance(review.get("grounded"), bool) or not review.get("reason"):
            raise ValueError("Grounding review needs a boolean verdict and reason")
        case["grounded_final_answer"] = review["grounded"]
        case["grounding_review"] = review["reason"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["scripted", "qwen", "openai"], default="scripted"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--review-report",
        type=Path,
        help="Apply manual verdicts to a saved report without re-running a model",
    )
    parser.add_argument("--reviews", type=Path)
    args = parser.parse_args()
    report = (
        json.loads(args.review_report.read_text(encoding="utf-8"))
        if args.review_report
        else evaluate_agent(settings=Settings(), mode=args.mode)
    )
    if args.reviews:
        apply_grounding_reviews(
            report, json.loads(args.reviews.read_text(encoding="utf-8"))
        )
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
        print(f"Saved {report['mode']} investigation report: {args.output}")
    else:
        print(encoded)


if __name__ == "__main__":
    main()
