"""Codex OAuth backend for AutoCedar's provider-neutral interface."""

from __future__ import annotations

from typing import Any, Sequence, TypeVar

from pydantic import BaseModel

from autocedar.codex_auth import CodexAuthClient, CodexCredentials

from .base import (
    ChatMessage,
    InstructionPart,
    ModelBackend,
    StructuredResult,
    TextResult,
)


_StructuredT = TypeVar("_StructuredT", bound=BaseModel)


class CodexOAuthBackend(ModelBackend):
    """Use the user's existing ``codex login`` session."""

    provider_id = "codex"

    def __init__(
        self,
        *,
        client: CodexAuthClient | None = None,
        credentials: CodexCredentials | None = None,
        requester: Any | None = None,
        timeout: float = 240.0,
    ) -> None:
        self._client = client or CodexAuthClient(
            credentials=credentials,
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
