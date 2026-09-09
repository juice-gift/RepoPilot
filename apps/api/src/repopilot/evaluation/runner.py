import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.session import (
    create_database_engine,
    create_database_session_factory,
)
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.evaluation.dataset import EvaluationCase, load_evaluation_dataset
from repopilot.evaluation.metrics import (
    EvidenceIdentity,
    calculate_metrics,
    first_relevant_rank,
)
from repopilot.indexing.service import index_snapshot
from repopilot.ingestion.service import ingest_repository
from repopilot.retrieval.retriever import RetrievalStrategy, retrieve_evidence

DEFAULT_EVALUATION_ROOT = REPOSITORY_ROOT / "apps" / "api" / "evaluation"


def evaluate_retrieval(
    *,
    database_url: str,
    repository_path: Path,
    dataset_path: Path,
    top_k: int = 5,
    strategy: RetrievalStrategy = "vector",
) -> dict[str, Any]:
    dataset = load_evaluation_dataset(dataset_path)
    provider = DeterministicEmbeddingProvider()
    engine = create_database_engine(database_url)
    session_factory = create_database_session_factory(engine)
    expected_rankings: list[tuple[EvidenceIdentity, ...]] = []
    retrieved_rankings: list[tuple[EvidenceIdentity, ...]] = []
    case_results: list[dict[str, Any]] = []
    try:
        with session_factory() as session:
            ingestion = ingest_repository(
                session,
                requested_path=str(repository_path),
                allowed_root=repository_path.parent,
                repository_name="RepoPilot V1 Golden Repository",
            )
            index = index_snapshot(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
                provider=provider,
            )
            for case in dataset.cases:
                retrieved = _retrieve_case(
                    session=session,
                    case=case,
                    repository_id=ingestion.repository.id,
                    snapshot_id=ingestion.snapshot.id,
                    provider=provider,
                    top_k=top_k,
                    strategy=strategy,
                )
                expected_rankings.append(case.expected_evidence)
                retrieved_rankings.append(retrieved)
                case_results.append(
                    {
                        "id": case.case_id,
                        "query": case.query,
                        "expected": [asdict(item) for item in case.expected_evidence],
                        "first_relevant_rank": first_relevant_rank(
                            case.expected_evidence, retrieved
                        ),
                        "retrieved": [asdict(item) for item in retrieved],
                    }
                )

            metrics = {
                f"k={k}": asdict(
                    calculate_metrics(
                        expected_rankings, retrieved_rankings, k=k
                    )
                )
                for k in sorted({1, min(3, top_k), top_k})
            }
            return {
                "dataset": dataset.name,
                "dataset_version": dataset.version,
                "strategy": (
                    "exact-vector-only"
                    if strategy == "vector"
                    else "exact-vector-plus-lexical-rerank"
                ),
                "provider": provider.provider_name,
                "model": provider.model_name,
                "dimensions": provider.dimensions,
                "repository_file_count": ingestion.snapshot.accepted_file_count,
                "chunk_count": index.chunk_count,
                "query_count": len(dataset.cases),
                "top_k": top_k,
                "metrics": metrics,
                "cases": case_results,
            }
    finally:
        engine.dispose()


def _retrieve_case(
    *,
    session: Session,
    case: EvaluationCase,
    repository_id: int,
    snapshot_id: int,
    provider: DeterministicEmbeddingProvider,
    top_k: int,
    strategy: RetrievalStrategy,
) -> tuple[EvidenceIdentity, ...]:
    result = retrieve_evidence(
        session,
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        question=case.query,
        top_k=top_k,
        provider=provider,
        strategy=strategy,
    )
    return tuple(
        EvidenceIdentity(item.file_path, item.symbol_name) for item in result.evidence
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RepoPilot V1 retrieval evaluation")
    parser.add_argument(
        "--repository",
        type=Path,
        default=DEFAULT_EVALUATION_ROOT / "golden_repository",
    )
    parser.add_argument(
        "--dataset", type=Path, default=DEFAULT_EVALUATION_ROOT / "dataset.json"
    )
    parser.add_argument("--top-k", type=int, default=5, choices=range(1, 21))
    parser.add_argument("--strategy", choices=("vector", "hybrid"), default="vector")
    args = parser.parse_args()
    report = evaluate_retrieval(
        database_url=Settings().database_url,
        repository_path=args.repository.resolve(),
        dataset_path=args.dataset.resolve(),
        top_k=args.top_k,
        strategy=args.strategy,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
