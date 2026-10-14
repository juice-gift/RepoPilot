"""Provider-independent request, observation and execution contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repository_id: int = Field(gt=0)
    snapshot_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=4_000)

    @field_validator("question")
    @classmethod
    def nonempty_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must not be empty")
        return value


class Evidence(BaseModel):
    evidence_id: str | None = None
    file_path: str
    language: str | None = None
    symbol_name: str | None = None
    qualified_name: str | None = None
    symbol_id: int | None = None
    start_line: int | None = None
    end_line: int | None = None
    content: str | None = None
    rank: int | None = None
    score: float | None = None
    distance: float | None = None
    truncated: bool = False


class Observation(BaseModel):
    status: Literal["ok", "error"] = "ok"
    items: list[Evidence] = Field(default_factory=list)
    omitted_items: int = 0
    truncated: bool = False
    error_code: str | None = None
    error_message: str | None = None


class ToolExecution(BaseModel):
    validated_arguments: dict[str, object] | None
    observation: Observation


class TraceStep(BaseModel):
    step: int
    model_turn: int
    call_id: str
    tool_name: str
    validated_arguments: dict[str, object] | None
    observation: Observation
    duration_ms: float


StopReason = Literal[
    "completed",
    "max_steps",
    "context_limit",
    "model_output_limit",
    "invalid_model_response",
    "provider_failure",
    "tool_failure",
]


class Diagnostics(BaseModel):
    provider: str
    model: str
    model_calls: int
    tool_failures: int
    input_character_count: int
    max_steps: int
    observation_character_limit: int
    context_character_limit: int
    model_output_character_limit: int
    duration_ms: float
    invalid_evidence_ids: list[str] = Field(default_factory=list)
    failure: str | None = None


class AgentResult(BaseModel):
    repository_id: int
    snapshot_id: int
    final_answer: str
    trace: list[TraceStep]
    sources: list[Evidence]
    total_steps: int
    stop_reason: StopReason
    diagnostics: Diagnostics
