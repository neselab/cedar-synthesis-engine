"""Direct OpenAI API backend using the official Responses SDK surface."""

from __future__ import annotations

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


DEFAULT_OPENAI_API_MODEL = "gpt-5.6"


class OpenAIAPIBackendError(RuntimeError):
    """Raised when direct OpenAI API configuration or output is invalid."""


class OpenAIAPIBackend(ModelBackend):
    """Use an OpenAI API key with the provider-neutral model contract."""

    provider_id = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: Any | None = None,
        timeout: float | None = None,
    ) -> None:
        if client is None:
            resolved_key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()
            if not resolved_key:
                raise OpenAIAPIBackendError(
                    "OpenAI API authentication is not configured. Set OPENAI_API_KEY.",
                )
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise OpenAIAPIBackendError(
                    "Direct OpenAI API support requires the 'openai' package.",
                ) from exc
            options: dict[str, Any] = {"api_key": resolved_key}
            if timeout is not None:
                options["timeout"] = timeout
            client = OpenAI(**options)
        self._client = client

    def generate_text(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        system: str | Sequence[InstructionPart] | None = None,
        max_tokens: int = 8192,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> TextResult:
        response = self._client.responses.create(**_responses_kwargs(
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        ))
        text = _response_text(response)
        return TextResult(
            text=text,
            usage=_openai_usage(getattr(response, "usage", None)),
            model=_string_field(response, "model") or model,
            request_id=_string_field(response, "id"),
        )

    def generate_structured(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        output_type: type[_StructuredT],
        system: str | Sequence[InstructionPart] | None = None,
        max_tokens: int = 8192,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> StructuredResult[_StructuredT]:
        response = self._client.responses.parse(
            **_responses_kwargs(
                model=model,
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                reasoning_effort=reasoning_effort,
            ),
            text_format=output_type,
        )
        value = getattr(response, "output_parsed", None)
        if value is None:
            value = _parsed_output_item(response)
        if value is None:
            raise OpenAIAPIBackendError(
                f"OpenAI returned no parsed {output_type.__name__} value.",
            )
        if not isinstance(value, output_type):
            value = output_type.model_validate(value)
        return StructuredResult(
            parsed=value,
            usage=_openai_usage(getattr(response, "usage", None)),
            model=_string_field(response, "model") or model,
            request_id=_string_field(response, "id"),
        )


_StructuredT = TypeVar("_StructuredT", bound=BaseModel)


def _responses_kwargs(
    *,
    model: str,
    messages: Sequence[ChatMessage],
    system: str | Sequence[InstructionPart] | None,
    max_tokens: int,
    temperature: float | None,
    reasoning_effort: str | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model or DEFAULT_OPENAI_API_MODEL,
        "input": [
            {"role": message.role, "content": message.content}
            for message in messages
        ],
        "store": False,
    }
    if isinstance(system, str):
        instructions = system
    else:
        instructions = "\n\n".join(part.text for part in (system or ()) if part.text.strip())
    if instructions:
        kwargs["instructions"] = instructions
    kwargs["max_output_tokens"] = max_tokens
    if reasoning_effort:
        kwargs["reasoning"] = {"effort": _openai_reasoning_effort(reasoning_effort)}
    if temperature is not None:
        kwargs["temperature"] = temperature
    return kwargs


def _openai_reasoning_effort(value: str) -> str:
    """Translate AutoCedar's public effort vocabulary to OpenAI's API."""

    normalized = value.strip().lower()
    return "xhigh" if normalized == "max" else normalized


def _response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts: list[str] = []
    output = getattr(response, "output", None)
    if isinstance(output, (list, tuple)):
        for item in output:
            content = _field(item, "content")
            if not isinstance(content, (list, tuple)):
                continue
            for block in content:
                text = _field(block, "text")
                block_type = _field(block, "type")
                if block_type in {"output_text", "text"} and isinstance(text, str):
                    parts.append(text)
    rendered = "\n".join(parts).strip()
    if not rendered:
        raise OpenAIAPIBackendError("OpenAI returned no text output.")
    return rendered


def _parsed_output_item(response: Any) -> Any | None:
    output = getattr(response, "output", None)
    if not isinstance(output, (list, tuple)):
        return None
    for item in output:
        content = _field(item, "content")
        if not isinstance(content, (list, tuple)):
            continue
        for block in content:
            parsed = _field(block, "parsed")
            if parsed is not None:
                return parsed
    return None


def _openai_usage(usage: Any) -> ModelUsage:
    input_details = _field(usage, "input_tokens_details")
    return ModelUsage(
        input_tokens=_nonnegative_int(_field(usage, "input_tokens")),
        output_tokens=_nonnegative_int(_field(usage, "output_tokens")),
        cache_read_input_tokens=_nonnegative_int(_field(input_details, "cached_tokens")),
        cache_creation_input_tokens=0,
    )


def _field(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _string_field(value: Any, name: str) -> str | None:
    field = _field(value, name)
    return field if isinstance(field, str) and field else None


def _nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(int(value), 0)
    return 0
