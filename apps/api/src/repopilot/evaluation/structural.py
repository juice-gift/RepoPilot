"""Frozen structural evaluation using the same persisted navigation as HTTP."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from repopilot.config import Settings
from repopilot.db.session import create_database_engine, create_database_session_factory
from repopilot.evaluation.runner import DEFAULT_EVALUATION_ROOT
from repopilot.ingestion.service import ingest_repository
from repopilot.intelligence.analysis import INDEX_VERSION, ResolutionStatus
from repopilot.intelligence.navigation import (
    SymbolMatch,
    SymbolView,
    find_references,
    get_definition,
    get_imports,
    list_files,
    search_symbols,
)
from repopilot.intelligence.service import index_structure

SymbolIdentity = tuple[str, str, int, int]
ImportIdentity = tuple[str, str, str | None, str | None, int, str | None]
ReferenceIdentity = tuple[str, str, int, ResolutionStatus, SymbolIdentity | None]


class StructuralQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str
    match: SymbolMatch
    expected: list[SymbolIdentity]


class StructuralDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    symbols: list[SymbolIdentity]
    queries: list[StructuralQuery]
    imports: list[ImportIdentity]
    references: list[ReferenceIdentity]


def load_structural_dataset(root: Path) -> StructuralDataset:
    manifest = json.loads(
        (root / "structural_manifest.json").read_text(encoding="utf-8")
    )
    for relative_path, expected_hash in manifest.items():
        path = (root / relative_path).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Structural manifest path escapes evaluation directory")
        actual_hash = hashlib.sha256(
            path.read_text(encoding="utf-8").replace("\r\n", "\n").encode()
        ).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Frozen structural input changed: {relative_path}")
    return StructuralDataset.model_validate_json(
        (root / "structural_dataset.json").read_text(encoding="utf-8")
    )


def _identity(symbol: SymbolView) -> SymbolIdentity:
    return symbol.file_path, symbol.qualified_name, symbol.start_line, symbol.end_line


def occurrence_metrics(
    expected: list[tuple], actual: list[tuple]
) -> dict[str, float | int]:
    # Multisets ensure duplicated outputs count as false positives.
    correct = sum((Counter(expected) & Counter(actual)).values())
    return {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "correct_count": correct,
        "precision": correct / len(actual) if actual else float(not expected),
        "recall": correct / len(expected) if expected else 1.0,
    }


def evaluate_snapshot(
    session: Session, repository_id: int, snapshot_id: int, dataset: StructuralDataset
) -> dict[str, object]:
    symbols = search_symbols(session, repository_id, snapshot_id, limit=500)
    by_id = {s.id: _identity(s) for s in symbols}
    actual_definitions = [
        _identity(get_definition(session, repository_id, snapshot_id, s.id).symbol)
        for s in symbols
    ]
    definitions = occurrence_metrics(dataset.symbols, actual_definitions)
    case_results = []
    for case in dataset.queries:
        found = [
            _identity(s)
            for s in search_symbols(
                session,
                repository_id,
                snapshot_id,
                query=case.query,
                match=case.match,
                limit=5,
            )
        ]
        rank = next(
            (i for i, item in enumerate(found, 1) if item in case.expected), None
        )
        case_results.append(
            {
                "query": case.query,
                "match": case.match,
                "expected": case.expected,
                "actual": found,
                "first_relevant_rank": rank,
            }
        )
    symbol_metrics = {}
    for k in (1, 3, 5):
        ranks = [result["first_relevant_rank"] for result in case_results]
        symbol_metrics[f"k={k}"] = {
            "hit_at_k": sum(rank is not None and rank <= k for rank in ranks)
            / len(ranks),
            "mrr_at_k": sum(
                1 / rank if rank is not None and rank <= k else 0 for rank in ranks
            )
            / len(ranks),
        }
    actual_imports: list[ImportIdentity] = []
    importer_errors = []
    for file in list_files(session, repository_id, snapshot_id, limit=500):
        for relation in get_imports(
            session, repository_id, snapshot_id, file.path, limit=500
        ):
            actual_imports.append(
                (
                    relation.file_path,
                    "." * relation.level + relation.module,
                    relation.imported_name,
                    relation.alias,
                    relation.line,
                    relation.target_file_path,
                )
            )
            if relation.target_file_path and relation.id not in {
                item.id
                for item in get_imports(
                    session,
                    repository_id,
                    snapshot_id,
                    relation.target_file_path,
                    reverse=True,
                    limit=500,
                )
            }:
                importer_errors.append(relation.id)
    refs = find_references(session, repository_id, snapshot_id, limit=500)
    actual_refs: list[ReferenceIdentity] = [
        (ref.file_path, ref.name, ref.line, ref.status, by_id.get(ref.target_symbol_id))
        for ref in refs
    ]
    expected_resolved = [r for r in dataset.references if r[3] == "resolved"]
    actual_resolved = [r for r in actual_refs if r[3] == "resolved"]
    reference_metrics = occurrence_metrics(expected_resolved, actual_resolved)
    all_reference_metrics = occurrence_metrics(dataset.references, actual_refs)
    bad_cases = {
        "missing_definitions": list(
            (Counter(dataset.symbols) - Counter(actual_definitions)).elements()
        ),
        "unexpected_definitions": list(
            (Counter(actual_definitions) - Counter(dataset.symbols)).elements()
        ),
        "missing_imports": list(
            (Counter(dataset.imports) - Counter(actual_imports)).elements()
        ),
        "unexpected_imports": list(
            (Counter(actual_imports) - Counter(dataset.imports)).elements()
        ),
        "missing_or_incorrect_references": list(
            (Counter(dataset.references) - Counter(actual_refs)).elements()
        ),
        "unexpected_references": list(
            (Counter(actual_refs) - Counter(dataset.references)).elements()
        ),
        "importer_errors": importer_errors,
    }
    return {
        "dataset_version": dataset.version,
        "index_version": INDEX_VERSION,
        "symbol_count": len(symbols),
        "query_count": len(dataset.queries),
        "symbol_retrieval": symbol_metrics,
        "definitions": definitions,
        "imports": occurrence_metrics(dataset.imports, actual_imports),
        "reference_resolution": reference_metrics,
        "reference_occurrences_and_status": all_reference_metrics,
        "reference_counts": dict(Counter(ref.status for ref in refs)),
        "bad_cases": bad_cases,
        "queries": case_results,
    }


def evaluate_structure(
    database_url: str, root: Path = DEFAULT_EVALUATION_ROOT
) -> dict[str, object]:
    dataset = load_structural_dataset(root)
    engine = create_database_engine(database_url)
    try:
        with create_database_session_factory(engine)() as session:
            ingestion = ingest_repository(
                session,
                requested_path=str(root / "structural_golden"),
                allowed_root=root,
                repository_name="RepoPilot V2 Structural Golden Repository",
            )
            index_structure(
                session,
                repository_id=ingestion.repository.id,
                snapshot_id=ingestion.snapshot.id,
            )
            return evaluate_snapshot(
                session, ingestion.repository.id, ingestion.snapshot.id, dataset
            )
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen RepoPilot V2 structural evaluation"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(
        evaluate_structure(Settings().database_url), indent=2, sort_keys=True
    )
    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()
