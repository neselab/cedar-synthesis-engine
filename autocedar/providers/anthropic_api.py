"""Anthropic API backend for AutoCedar's provider-neutral model contract."""

from __future__ import annotations

import json
import os
from typing import Any, Sequence, TypeVar

from pydantic import BaseModel

from .base import (
    ChatMessage,
    InstructionPart,
    ModelBackend,
    ModelUsage,
    StructuredResult,
    TextResult,
)


DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-7"
DEFAULT_MAX_OUTPUT_TOKENS = 16_000


class AnthropicBackendError(RuntimeError):
    """Raised when Anthropic cannot produce a usable model response."""


class AnthropicAPIBackend(ModelBackend):
    """Use the official Anthropic SDK behind the neutral backend interface.

    This is deliberately the only AutoCedar backend that knows about
    ``messages.create`` and ``messages.parse``.  Provider-specific prompt
    caching and the structured-output grammar fallback stay at this boundary.
    """

    provider_id = "anthropic"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        if client is None:
            from anthropic import Anthropic

            resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "").strip()
            if not resolved_key:
                raise AnthropicBackendError(
                    "Anthropic API authentication is not configured. Set ANTHROPIC_API_KEY.",
                )
            client = Anthropic(api_key=resolved_key)
        self._client = client

    def generate_text(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        system: str | Sequence[InstructionPart] | None = None,
        max_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> TextResult:
        response = self._client.messages.create(**_anthropic_kwargs(
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        ))
        return TextResult(
            text=_first_text(response),
            usage=_anthropic_usage(getattr(response, "usage", None)),
            model=_response_field(response, "model") or model,
            request_id=_response_field(response, "id"),
        )

    def generate_structured(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        output_type: type[_StructuredT],
        system: str | Sequence[InstructionPart] | None = None,
        max_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> StructuredResult[_StructuredT]:
        kwargs = _anthropic_kwargs(
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        )
        try:
            response = self._client.messages.parse(
                **kwargs,
                output_format=output_type,
            )
        except Exception as exc:
            if not _is_grammar_compilation_timeout(exc):
                raise
            return self._grammar_fallback(
                model=model,
                messages=messages,
                output_type=output_type,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                reasoning_effort=reasoning_effort,
            )

        parsed = getattr(response, "parsed_output", None)
        if parsed is None:
            raise AnthropicBackendError(
                f"Anthropic returned no parsed {output_type.__name__} value.",
            )
        return StructuredResult(
            parsed=parsed,
            usage=_anthropic_usage(getattr(response, "usage", None)),
            model=_response_field(response, "model") or model,
            request_id=_response_field(response, "id"),
        )

    def _grammar_fallback(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        output_type: type[_StructuredT],
        system: str | Sequence[InstructionPart] | None,
        max_tokens: int,
        temperature: float | None,
        reasoning_effort: str | None,
    ) -> StructuredResult[_StructuredT]:
        schema = json.dumps(output_type.model_json_schema(), indent=2, sort_keys=True)
        fallback_instruction = (
            "The structured-output grammar compiler timed out. Return only a JSON "
            "object matching this JSON Schema. Do not wrap it in Markdown and do "
            "not include explanatory prose.\n\n"
            f"```json\n{schema}\n```"
        )
        fallback_messages = tuple(messages) + (
            ChatMessage(role="user", content=fallback_instruction),
        )
        response = self._client.messages.create(**_anthropic_kwargs(
            model=model,
            messages=fallback_messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        ))
        text = _first_text(response)
        try:
            parsed = output_type.model_validate(_extract_json_object(text))
        except Exception as exc:
            raise AnthropicBackendError(
                f"Anthropic returned invalid {output_type.__name__} JSON: {exc}",
            ) from exc
        return StructuredResult(
            parsed=parsed,
            usage=_anthropic_usage(getattr(response, "usage", None)),
            model=_response_field(response, "model") or model,
            request_id=_response_field(response, "id"),
        )


_StructuredT = TypeVar("_StructuredT", bound=BaseModel)


def _anthropic_kwargs(
    *,
    model: str,
    messages: Sequence[ChatMessage],
    system: str | Sequence[InstructionPart] | None,
    max_tokens: int,
    temperature: float | None,
    reasoning_effort: str | None,
) -> dict[str, Any]:
    message_system_parts = [
        InstructionPart(text=message.content)
        for message in messages
        if message.role == "system"
    ]
    kwargs: dict[str, Any] = {
        "model": model or DEFAULT_ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role != "system"
        ],
    }
    if isinstance(system, str):
        system_parts = ([InstructionPart(text=system)] if system else []) + message_system_parts
    else:
        system_parts = list(system or ()) + message_system_parts
    if system_parts:
        kwargs["system"] = [
            {
                "type": "text",
                "text": part.text,
                **(
                    {"cache_control": {"type": "ephemeral"}}
                    if part.cache_hint == "ephemeral"
                    else {}
                ),
            }
            for part in system_parts
        ]
    if reasoning_effort:
        kwargs["thinking"] = {"type": "adaptive"}
        kwargs["output_config"] = {"effort": reasoning_effort}
    if temperature is not None:
        kwargs["temperature"] = temperature
    return kwargs


def _first_text(response: Any) -> str:
    content = getattr(response, "content", None)
    if not isinstance(content, (list, tuple)):
        raise AnthropicBackendError("Anthropic returned no content blocks.")
    parts: list[str] = []
    for block in content:
        block_type = getattr(block, "type", None)
        text = getattr(block, "text", None)
        if isinstance(block, dict):
            block_type = block.get("type")
            text = block.get("text")
        if block_type == "text" and isinstance(text, str):
            parts.append(text)
    rendered = "\n".join(parts).strip()
    if not rendered:
        raise AnthropicBackendError("Anthropic returned no text output.")
    return rendered


def _anthropic_usage(usage: Any) -> ModelUsage:
    return ModelUsage(
        input_tokens=_nonnegative_int(_field(usage, "input_tokens")),
        output_tokens=_nonnegative_int(_field(usage, "output_tokens")),
        cache_read_input_tokens=_nonnegative_int(
            _field(usage, "cache_read_input_tokens"),
        ),
        cache_creation_input_tokens=_nonnegative_int(
            _field(usage, "cache_creation_input_tokens"),
        ),
    )


def _field(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _response_field(value: Any, name: str) -> str | None:
    field = _field(value, name)
    return field if isinstance(field, str) and field else None


def _nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(int(value), 0)
    return 0


def _is_grammar_compilation_timeout(exc: Exception) -> bool:
    return "grammar compilation timed out" in str(exc).lower()


def _extract_json_object(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(stripped[start : end + 1])
