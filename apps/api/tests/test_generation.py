from types import SimpleNamespace
from unittest.mock import MagicMock

from repopilot.rag.generation import OpenAIResponsesGenerationProvider


def test_openai_generation_uses_responses_api_without_storage() -> None:
    client = MagicMock()
    client.responses.create.return_value = SimpleNamespace(output_text=" Answer [E1]. ")
    provider = OpenAIResponsesGenerationProvider(
        api_key="test",
        model_name="gpt-5.6-luna",
        max_output_tokens=1200,
        client=client,
    )

    answer = provider.generate(instructions="instructions", input_text="input")

    assert answer == "Answer [E1]."
    client.responses.create.assert_called_once_with(
        model="gpt-5.6-luna",
        instructions="instructions",
        input="input",
        max_output_tokens=1200,
        reasoning={"effort": "none"},
        store=False,
    )
