import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.db.session import (
    create_database_engine,
    create_database_session_factory,
)
from repopilot.embeddings.providers import (
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
    QwenEmbeddingProvider,
)
from repopilot.evaluation.dataset import load_evaluation_dataset
from repopilot.evaluation.metrics import EvidenceIdentity, evidence_matches
from repopilot.indexing.service import index_snapshot
from repopilot.ingestion.service import ingest_repository
from repopilot.rag.generation import (
    GenerationProvider,
    OpenAIResponsesGenerationProvider,
    QwenResponsesGenerationProvider,
)
from repopilot.rag.service import answer_repository_question

DEFAULT_EVALUATION_ROOT = REPOSITORY_ROOT / "apps" / "api" / "evaluation"
LiveProviderName = Literal["openai", "qwen"]


class LiveProviderValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class LiveProviderValidationResult:
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    generation_provider: str
    generation_model: str
    retrieval_strategy: str
    repository_file_count: int
    chunk_count: int
    question: str
    expected_first_rank: int | None
    citation_count: int
    cited_files: tuple[str, ...]
    answer: str


def run_live_provider_validation(
    *,
    settings: Settings,
    repository_path: Path,
    dataset_path: Path,
    case_id: str,
    provider_name: LiveProviderName = "qwen",
) -> LiveProviderValidationResult:
    embedding_provider, generation_provider = _create_live_providers(
        settings, provider_name
    )

    dataset = load_evaluation_dataset(dataset_path)
    case = next((item for item in dataset.cases if item.case_id == case_id), None)
    if case is None:
        raise LiveProviderValidationError(f"Unknown evaluation case: {case_id}")

    engine = create_database_engine(settings.database_url)
    session_factory = create_database_session_factory(engine)
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
                provider=embedding_provider,
            )
            result = answer_repository_question(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
                question=case.query,
                top_k=5,
                context_character_limit=settings.context_character_limit,
                context_max_evidence=settings.context_max_evidence,
                embedding_provider=embedding_provider,
                generation_provider=generation_provider,
                retrieval_strategy="hybrid",
            )
    finally:
        engine.dispose()

    if result.status != "answered" or not result.citations.citations:
        raise LiveProviderValidationError(
            "Live generation did not return an answer with a valid evidence citation"
        )
    expected_first_rank = next(
        (
            evidence.rank
            for evidence in result.retrieval.evidence
            if any(
                evidence_matches(
                    expected,
                    EvidenceIdentity(evidence.file_path, evidence.symbol_name),
                )
                for expected in case.expected_evidence
            )
        ),
        None,
    )
    return LiveProviderValidationResult(
        embedding_provider=embedding_provider.provider_name,
        embedding_model=embedding_provider.model_name,
        embedding_dimensions=embedding_provider.dimensions,
        generation_provider=generation_provider.provider_name,
        generation_model=generation_provider.model_name,
        retrieval_strategy=result.retrieval.retrieval_strategy,
        repository_file_count=ingestion.snapshot.accepted_file_count,
        chunk_count=index.chunk_count,
        question=case.query,
        expected_first_rank=expected_first_rank,
        citation_count=len(result.citations.citations),
        cited_files=tuple(
            citation.file_path for citation in result.citations.citations
        ),
        answer=result.answer,
    )


def _create_live_providers(
    settings: Settings, provider_name: LiveProviderName
) -> tuple[EmbeddingProvider, GenerationProvider]:
    if provider_name == "qwen":
        api_key = (
            settings.dashscope_api_key.get_secret_value().strip()
            if settings.dashscope_api_key
            else ""
        )
        if not api_key:
            raise LiveProviderValidationError(
                "DASHSCOPE_API_KEY is required for Qwen live provider validation"
            )
        return (
            QwenEmbeddingProvider(
                api_key=api_key,
                base_url=settings.dashscope_base_url,
                model_name=settings.qwen_embedding_model,
                dimensions=settings.embedding_dimensions,
            ),
            QwenResponsesGenerationProvider(
                api_key=api_key,
                base_url=settings.dashscope_base_url,
                model_name=settings.qwen_generation_model,
                max_output_tokens=settings.generation_max_output_tokens,
            ),
        )

    api_key = (
        settings.openai_api_key.get_secret_value().strip()
        if settings.openai_api_key
        else ""
    )
    if not api_key:
        raise LiveProviderValidationError(
            "OPENAI_API_KEY is required for OpenAI live provider validation"
        )
    return (
        OpenAIEmbeddingProvider(
            api_key=api_key,
            model_name=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
        ),
        OpenAIResponsesGenerationProvider(
            api_key=api_key,
            model_name=settings.generation_model,
            max_output_tokens=settings.generation_max_output_tokens,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate RepoPilot against a configured live AI provider"
    )
    parser.add_argument("--provider", choices=("qwen", "openai"), default="qwen")
    parser.add_argument(
        "--repository",
        type=Path,
        default=DEFAULT_EVALUATION_ROOT / "golden_repository",
    )
    parser.add_argument(
        "--dataset", type=Path, default=DEFAULT_EVALUATION_ROOT / "dataset.json"
    )
    parser.add_argument("--case", default="missing-database-url")
    args = parser.parse_args()
    try:
        result = run_live_provider_validation(
            settings=Settings(),
            repository_path=args.repository.resolve(),
            dataset_path=args.dataset.resolve(),
            case_id=args.case,
            provider_name=args.provider,
        )
    except LiveProviderValidationError as error:
        parser.error(str(error))
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
