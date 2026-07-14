"""Local OpenAI-compatible backend (vLLM and similar servers)."""

from __future__ import annotations

from typing import Any, Sequence, TypeVar

from pydantic import BaseModel

from autocedar.openai_compatible import OpenAICompatibleClient

from .base import (
    ChatMessage,
    InstructionPart,
    ModelBackend,
    StructuredResult,
    TextResult,
)


_StructuredT = TypeVar("_StructuredT", bound=BaseModel)


class LocalOpenAIBackend(ModelBackend):
    """Use a user-configured local OpenAI-compatible HTTP endpoint."""

    provider_id = "local"

    def __init__(
        self,
        *,
        client: OpenAICompatibleClient | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        requester: Any | None = None,
        timeout: float = 600.0,
    ) -> None:
        self._client = client or OpenAICompatibleClient(
            base_url=base_url,
            api_key=api_key,
            requester=requester,
            timeout=timeout,
        )

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
        return self._client.generate_text(
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
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
        return self._client.generate_structured(
            model=model,
            messages=messages,
            output_type=output_type,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        )
