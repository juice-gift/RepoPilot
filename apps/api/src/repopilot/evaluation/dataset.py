import json
from dataclasses import dataclass
from pathlib import Path

from repopilot.evaluation.metrics import EvidenceIdentity


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    query: str
    expected_evidence: tuple[EvidenceIdentity, ...]


@dataclass(frozen=True)
class EvaluationDataset:
    name: str
    version: int
    cases: tuple[EvaluationCase, ...]


def load_evaluation_dataset(path: Path) -> EvaluationDataset:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not load evaluation dataset: {error}") from error
    if not isinstance(payload, dict):
        raise TypeError("Evaluation dataset must be a JSON object")

    name = payload.get("name")
    version = payload.get("version")
    raw_cases = payload.get("cases")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Evaluation dataset name is required")
    if not isinstance(version, int) or version < 1:
        raise ValueError("Evaluation dataset version must be a positive integer")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Evaluation dataset must contain at least one case")

    cases: list[EvaluationCase] = []
    seen_case_ids: set[str] = set()
    for raw_case in raw_cases:
        case = _parse_case(raw_case)
        if case.case_id in seen_case_ids:
            raise ValueError(f"Duplicate evaluation case id: {case.case_id}")
        seen_case_ids.add(case.case_id)
        cases.append(case)
    return EvaluationDataset(name=name, version=version, cases=tuple(cases))


def _parse_case(raw_case: object) -> EvaluationCase:
    if not isinstance(raw_case, dict):
        raise TypeError("Each evaluation case must be a JSON object")
    case_id = raw_case.get("id")
    query = raw_case.get("query")
    raw_expected = raw_case.get("expected_evidence")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("Every evaluation case requires an id")
    if not isinstance(query, str) or not query.strip():
        raise ValueError(f"Evaluation case {case_id!r} requires a query")
    if not isinstance(raw_expected, list) or not raw_expected:
        raise ValueError(f"Evaluation case {case_id!r} requires expected evidence")

    expected: list[EvidenceIdentity] = []
    for item in raw_expected:
        if not isinstance(item, dict):
            raise TypeError(f"Expected evidence in {case_id!r} must be an object")
        file_path = item.get("file_path")
        symbol_name = item.get("symbol_name")
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError(f"Expected evidence in {case_id!r} needs file_path")
        if symbol_name is not None and not isinstance(symbol_name, str):
            raise ValueError(f"symbol_name in {case_id!r} must be a string or null")
        expected.append(EvidenceIdentity(file_path, symbol_name))
    return EvaluationCase(case_id, query.strip(), tuple(expected))
