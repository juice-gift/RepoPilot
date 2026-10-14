"""Small Responses tool-calling boundary; SDK objects do not leave this module."""

import json
from dataclasses import dataclass
from typing import Protocol, cast

from openai import OpenAI
from openai.types.responses import ResponseInputItemParam, ToolParam


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class AgentTurn:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    incomplete: bool = False


class AgentProvider(Protocol):
    provider_name: str
    model_name: str

    def complete(
        self,
        *,
        instructions: str,
        history: list[dict[str, object]],
        tools: list[dict[str, object]],
    ) -> AgentTurn: ...


def complete_response(
    client: OpenAI,
    *,
    model: str,
    max_output_tokens: int,
    instructions: str,
    history: list[dict[str, object]],
    tools: list[dict[str, object]],
) -> AgentTurn:
    response = client.with_options(timeout=30, max_retries=0).responses.create(
        model=model,
        instructions=instructions,
        input=cast(list[ResponseInputItemParam], history),
        tools=cast(list[ToolParam], tools),
        max_output_tokens=max_output_tokens,
        reasoning={"effort": "none"},
        store=False,
    )
    calls: list[ToolCall] = []
    for item in response.output:
        if item.type == "function_call":
            calls.append(
                ToolCall(call_id=item.call_id, name=item.name, arguments=item.arguments)
            )
        elif item.type not in ("message", "reasoning"):
            raise ValueError("Unexpected provider output type")
    # Text alongside a tool call is not a final answer. Reasoning is never copied.
    return AgentTurn(
        text="" if calls else response.output_text,
        tool_calls=tuple(calls),
        incomplete=response.status != "completed",
    )


class DeterministicAgentProvider:
    """Zero-cost workflow aid, explicitly not a model-quality substitute."""

    provider_name = "deterministic"
    model_name = "deterministic-investigation-v3"

    def complete(
        self,
        *,
        instructions: str,
        history: list[dict[str, object]],
        tools: list[dict[str, object]],
    ) -> AgentTurn:
        del instructions, tools
        observations = [h for h in history if h.get("type") == "function_call_output"]
        if not observations:
            return AgentTurn(
                tool_calls=(
                    ToolCall(
                        "local_retrieve",
                        "retrieve_context",
                        json.dumps({"query": history[0]["content"], "top_k": 3}),
                    ),
                )
            )
        observation = json.loads(str(observations[-1]["output"]))
        items = observation.get("items", [])
        if len(observations) == 1 and items:
            item = items[0]
            start = item["start_line"]
            return AgentTurn(
                tool_calls=(
                    ToolCall(
                        "local_read",
                        "read_file",
                        json.dumps(
                            {
                                "path": item["file_path"],
                                "start_line": start,
                                "end_line": min(item["end_line"], start + 199),
                            }
                        ),
                    ),
                )
            )
        if not items:
            return AgentTurn(
                text="The deterministic workflow did not obtain source evidence. Check the tool failure or snapshot index."
            )
        return AgentTurn(
            text=(
                "This deterministic workflow retrieved and inspected saved source "
                f"[{items[0]['evidence_id']}]. Inspect the evidence for implementation details; "
                "this local provider does not perform LLM investigation."
            )
        )
