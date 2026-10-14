from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from repopilot.config import Settings
from repopilot.rag.generation import (
    GenerationConfigurationError,
    OpenAIResponsesGenerationProvider,
    QwenResponsesGenerationProvider,
    create_agent_provider,
)
from repopilot.rag.tool_calling import DeterministicAgentProvider


@pytest.mark.parametrize(
    "provider_type",
    [QwenResponsesGenerationProvider, OpenAIResponsesGenerationProvider],
)
def test_responses_boundary_keeps_calls_and_discards_reasoning(provider_type):
    client = MagicMock()
    client.with_options.return_value = client
    client.responses.create.return_value = SimpleNamespace(
        status="completed",
        output_text="Intermediate reasoning must not be replayed",
        output=[
            SimpleNamespace(type="reasoning", summary="private thoughts"),
            SimpleNamespace(
                type="function_call",
                call_id="c1",
                name="read_file",
                arguments='{"path":"a.py"}',
            ),
        ],
    )
    kwargs = {
        "api_key": "test",
        "model_name": "test-model",
        "max_output_tokens": 1200,
        "client": client,
    }
    if provider_type is QwenResponsesGenerationProvider:
        kwargs["base_url"] = "https://example.invalid"
    provider = provider_type(**kwargs)
    history = [{"role": "user", "content": "inspect"}]
    tools = [
        {"type": "function", "name": "read_file", "parameters": {"type": "object"}}
    ]
    turn = provider.complete(instructions="safe", history=history, tools=tools)
    assert turn.text == "" and len(turn.tool_calls) == 1
    assert turn.tool_calls[0].call_id == "c1"
    assert "private" not in str(turn)
    request = client.responses.create.call_args.kwargs
    assert request == {
        "model": "test-model",
        "instructions": "safe",
        "input": history,
        "tools": tools,
        "max_output_tokens": 1200,
        "reasoning": {"effort": "none"},
        "store": False,
    }
    client.with_options.assert_called_once_with(timeout=30, max_retries=0)


def test_factory_deterministic_and_missing_key():
    settings = Settings(
        database_url="postgresql+psycopg://u:p@localhost/db",
        _env_file=None,
        generation_provider="deterministic",
    )
    assert isinstance(create_agent_provider(settings), DeterministicAgentProvider)
    settings.generation_provider = "qwen"
    settings.dashscope_api_key = None
    with pytest.raises(GenerationConfigurationError, match="DASHSCOPE_API_KEY"):
        create_agent_provider(settings)
