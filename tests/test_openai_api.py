from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

from autocedar.providers.base import ChatMessage, InstructionPart
from autocedar.providers.openai_api import OpenAIAPIBackend


class Answer(BaseModel):
    answer: str


class FakeResponses:
    def __init__(self) -> None:
        self.create_kwargs: dict[str, Any] | None = None
        self.parse_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> Any:
        self.create_kwargs = kwargs
        return SimpleNamespace(
            id="resp_1",
            model=kwargs["model"],
            output_text="plain",
            usage=SimpleNamespace(
                input_tokens=20,
                output_tokens=5,
                input_tokens_details=SimpleNamespace(cached_tokens=7),
            ),
        )

    def parse(self, **kwargs: Any) -> Any:
        self.parse_kwargs = kwargs
        return SimpleNamespace(
            id="resp_2",
            model=kwargs["model"],
            output_parsed=Answer(answer="yes"),
            usage=SimpleNamespace(input_tokens=10, output_tokens=3),
        )


def test_openai_backend_uses_responses_and_normalizes_usage() -> None:
    responses = FakeResponses()
    backend = OpenAIAPIBackend(client=SimpleNamespace(responses=responses))

    result = backend.generate_text(
        model="gpt-test",
        system=(InstructionPart("first"), InstructionPart("second")),
        messages=(ChatMessage(role="user", content="hello"),),
        max_tokens=321,
        reasoning_effort="max",
        temperature=0.1,
    )

    assert result.text == "plain"
    assert result.usage.cache_read_input_tokens == 7
    assert responses.create_kwargs == {
        "model": "gpt-test",
        "input": [{"role": "user", "content": "hello"}],
        "store": False,
        "instructions": "first\n\nsecond",
        "max_output_tokens": 321,
        "reasoning": {"effort": "xhigh"},
        "temperature": 0.1,
    }


def test_openai_structured_uses_responses_parse_with_pydantic_type() -> None:
    responses = FakeResponses()
    backend = OpenAIAPIBackend(client=SimpleNamespace(responses=responses))

    result = backend.generate_structured(
        model="gpt-test",
        system="system",
        messages=(ChatMessage(role="user", content="question"),),
        output_type=Answer,
    )

    assert result.parsed == Answer(answer="yes")
    assert responses.parse_kwargs is not None
    assert responses.parse_kwargs["text_format"] is Answer
    assert responses.parse_kwargs["instructions"] == "system"
