"""Versioned V6 contracts; hashes bind evaluator inputs, never model prompts."""

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from repopilot.evaluation.runner import DEFAULT_EVALUATION_ROOT

Category = Literal["retrieval", "structure", "investigation", "rag", "resolution"]
Status = Literal[
    "passed",
    "failed",
    "not_applicable",
    "not_run",
    "unverified",
    "provider_error",
    "infrastructure_error",
]


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Task(Contract):
    id: str = Field(min_length=1)
    category: Category
    source_id: str = Field(min_length=1)
    expected: Literal[
        "evidence", "structure", "review", "verified_repair", "needs_owner_decision"
    ]
    legacy_id: str = Field(min_length=1)
    evidence: list[dict[str, str | None]] = Field(default_factory=list)
    question: str | None = None
    claim_check: str | None = None


class Dataset(Contract):
    name: str
    version: Literal[1]
    files: dict[str, str]
    tasks: list[Task] = Field(min_length=1)

    @model_validator(mode="after")
    def unique(self) -> "Dataset":
        if len({t.id for t in self.tasks}) != len(self.tasks):
            raise ValueError("Duplicate task IDs")
        allowed = {
            "retrieval": {"evidence"},
            "structure": {"structure"},
            "investigation": {"review"},
            "rag": {"review"},
            "resolution": {"verified_repair", "needs_owner_decision"},
        }
        for task in self.tasks:
            if task.expected not in allowed[task.category]:
                raise ValueError("Category/outcome mismatch")
        return self


def load_dataset(
    path: Path = DEFAULT_EVALUATION_ROOT / "v6-dataset.json",
    root: Path = DEFAULT_EVALUATION_ROOT,
) -> Dataset:
    dataset = Dataset.model_validate_json(path.read_text(encoding="utf-8"))
    # Pin the complete contract, including task criteria, separately from its files.
    expected = (root / "v6-dataset.sha256").read_text().strip()
    if digest(dataset.model_dump()) != expected:
        raise ValueError("Dataset contract hash mismatch")
    for relative, expected_hash in dataset.files.items():
        target = (root / relative).resolve()
        if not target.is_relative_to(root.resolve()) or target.is_symlink():
            raise ValueError("Unsafe dataset path")
        if file_digest(target) != expected_hash:
            raise ValueError(f"Frozen input changed: {relative}")
    for directory in (
        "golden_repository",
        "structural_golden",
        "agent_golden",
        "resolution_golden",
    ):
        actual = {
            p.relative_to(root).as_posix()
            for p in (root / directory).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }
        declared = {p for p in dataset.files if p.startswith(directory + "/")}
        if actual != declared:
            raise ValueError(f"Frozen file set changed: {directory}")
    return dataset


class CaseResult(Contract):
    id: str
    category: Category
    status: Status
    checks: dict[str, Status] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)
    evidence: dict[str, object] = Field(default_factory=dict)
    latency_ms: float | None = None
    tool_calls: int | None = None
    model_turns: int | None = None
    tokens: int | None = None
    cost: float | None = None
