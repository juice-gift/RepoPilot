"""Resolution contracts are separate from V3 source-only observations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from repopilot.resolution.patch import ChangedFile, PatchRecord
from repopilot.resolution.sandbox import TestResult

CaseId = Literal["fee-days", "dispatch-preconditions", "ambiguous-cap"]


class ResolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repository_id: int = Field(gt=0)
    snapshot_id: int = Field(gt=0)
    profile: CaseId
    issue: str = Field(min_length=1, max_length=4000)

    @field_validator("issue")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Issue must not be blank")
        return value.strip()


class ResolutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0, le=20)
    decision: Literal["repair", "needs_owner_decision", "insufficient_evidence"]
    summary: str = Field(min_length=1, max_length=2000)
    steps: list[str] = Field(min_length=1, max_length=6)
    files: list[str] = Field(max_length=6)

    @field_validator("summary")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Plan summary must not be blank")
        return value

    @field_validator("steps")
    @classmethod
    def bounded_steps(cls, steps: list[str]) -> list[str]:
        if any(not step.strip() or len(step) > 500 for step in steps):
            raise ValueError("Plan steps must be nonempty and bounded")
        return steps


class ResolutionObservation(BaseModel):
    status: Literal["ok", "error"] = "ok"
    payload: dict[str, object] = Field(default_factory=dict)
    error_code: str | None = None
    truncated: bool = False


class ResolutionTrace(BaseModel):
    step: int
    model_turn: int
    call_id: str
    tool_name: str
    arguments: dict[str, object] | None
    observation: ResolutionObservation
    duration_ms: float


class ResolutionDiagnostics(BaseModel):
    provider: str
    model: str
    model_calls: int
    patch_attempts: int
    test_executions: int
    duration_ms: float
    limits: dict[str, int | float]
    failure: str | None = None


ResolutionStop = Literal[
    "completed",
    "max_steps",
    "context_limit",
    "model_output_limit",
    "invalid_model_response",
    "provider_failure",
    "tool_failure",
    "patch_limit",
    "test_limit",
    "wall_time_limit",
    "sandbox_failure",
]


class ResolutionResult(BaseModel):
    repository_id: int
    snapshot_id: int
    workspace_id: str
    revision: int
    profile: CaseId
    execution_status: Literal["completed", "stopped"]
    repair_status: Literal[
        "verified_repair",
        "incomplete_repair",
        "insufficient_evidence",
        "needs_owner_decision",
    ]
    final_answer: str
    plans: list[ResolutionPlan]
    patch: str
    changed_files: list[ChangedFile]
    patch_history: list[PatchRecord]
    test_results: list[TestResult]
    trace: list[ResolutionTrace]
    stop_reason: ResolutionStop
    diagnostics: ResolutionDiagnostics
    workspace_cleaned: bool = False
