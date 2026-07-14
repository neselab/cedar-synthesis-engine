from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

from autocedar.providers.anthropic_api import AnthropicAPIBackend
from autocedar.providers.base import ChatMessage, InstructionPart


class Answer(BaseModel):
    answer: str


class FakeMessages:
    def __init__(self) -> None:
        self.create_kwargs: list[dict[str, Any]] = []
        self.parse_kwargs: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.create_kwargs.append(kwargs)
        return SimpleNamespace(
            id="msg_1",
            model=kwargs["model"],
            content=[SimpleNamespace(type="text", text='{"answer":"fallback"}')],
            usage=SimpleNamespace(
                input_tokens=12,
                output_tokens=4,
                cache_read_input_tokens=8,
                cache_creation_input_tokens=2,
            ),
        )

    def parse(self, **kwargs: Any) -> Any:
        self.parse_kwargs.append(kwargs)
        return SimpleNamespace(
            id="msg_2",
            model=kwargs["model"],
            parsed_output=Answer(answer="parsed"),
            usage=SimpleNamespace(input_tokens=9, output_tokens=3),
        )


def test_anthropic_backend_maps_cache_hints_and_normalizes_usage() -> None:
    messages = FakeMessages()
    backend = AnthropicAPIBackend(client=SimpleNamespace(messages=messages))

    result = backend.generate_text(
        model="claude-test",
        system=(
            InstructionPart("stable"),
            InstructionPart("spec", cache_hint="ephemeral"),
        ),
        messages=(ChatMessage(role="user", content="hello"),),
        max_tokens=123,
        reasoning_effort="max",
        temperature=0.2,
    )

    assert result.text == '{"answer":"fallback"}'
    assert result.usage.input_tokens == 12
    assert result.usage.cache_read_input_tokens == 8
    assert result.usage.cache_creation_input_tokens == 2
    sent = messages.create_kwargs[0]
    assert sent["messages"] == [{"role": "user", "content": "hello"}]
    assert sent["system"][0] == {"type": "text", "text": "stable"}
    assert sent["system"][1]["cache_control"] == {"type": "ephemeral"}
    assert sent["thinking"] == {"type": "adaptive"}
    assert sent["output_config"] == {"effort": "max"}


def test_anthropic_structured_uses_parse_at_provider_boundary() -> None:
    messages = FakeMessages()
    backend = AnthropicAPIBackend(client=SimpleNamespace(messages=messages))

    result = backend.generate_structured(
        model="claude-test",
        system="system",
        messages=(ChatMessage(role="user", content="question"),),
        output_type=Answer,
    )

    assert result.parsed == Answer(answer="parsed")
    assert messages.parse_kwargs[0]["output_format"] is Answer
    assert not messages.create_kwargs


def test_anthropic_grammar_timeout_falls_back_to_prompted_json() -> None:
    messages = FakeMessages()

    def timed_out(**kwargs: Any) -> Any:
        messages.parse_kwargs.append(kwargs)
        raise RuntimeError("grammar compilation timed out while building schema")

    messages.parse = timed_out  # type: ignore[method-assign]
    backend = AnthropicAPIBackend(client=SimpleNamespace(messages=messages))

    result = backend.generate_structured(
        model="claude-test",
        messages=(ChatMessage(role="user", content="question"),),
        output_type=Answer,
    )

    assert result.parsed.answer == "fallback"
    fallback_turn = messages.create_kwargs[0]["messages"][-1]["content"]
    assert "grammar compiler timed out" in fallback_turn
    assert '"answer"' in fallback_turn
