"""Provider-neutral model backend contract.

The rest of AutoCedar talks to :class:`ModelBackend`, never to a vendor SDK.
Provider adapters are responsible for translating this small contract into
Codex Responses, Claude CLI, Anthropic Messages, OpenAI Responses, or a local
OpenAI-compatible HTTP request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Literal, Mapping, Protocol, Sequence, TypeVar, runtime_checkable

from pydantic import BaseModel


MessageRole = Literal["user", "assistant", "system"]
CacheHint = Literal["none", "ephemeral"]
StructuredT = TypeVar("StructuredT", bound=BaseModel)


class ProviderError(RuntimeError):
    """Base exception for provider configuration and runtime failures."""


class ProviderConfigurationError(ProviderError, ValueError):
    """Raised when a provider or model setting is invalid."""


class BackendUnavailableError(ProviderError):
    """Raised when a configured backend cannot be loaded or used."""


@dataclass(frozen=True)
class ChatMessage:
    """One provider-independent chat turn."""

    role: MessageRole
    content: str

    def __post_init__(self) -> None:
        if self.role not in {"user", "assistant", "system"}:
            raise ProviderConfigurationError(f"Unsupported message role: {self.role!r}")
        if not isinstance(self.content, str) or not self.content:
            raise ProviderConfigurationError("Message content must be a non-empty string.")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ChatMessage":
        """Convert a plain ``{"role": ..., "content": ...}`` mapping."""

        role = value.get("role")
        content = value.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            raise ProviderConfigurationError(
                "Messages require string 'role' and 'content' fields.",
            )
        return cls(role=role, content=content)  # type: ignore[arg-type]


@dataclass(frozen=True)
class InstructionPart:
    """A system-instruction segment with a provider-neutral cache hint."""

    text: str
    cache_hint: CacheHint = "none"

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text:
            raise ProviderConfigurationError("Instruction text must be non-empty.")
        if self.cache_hint not in {"none", "ephemeral"}:
            raise ProviderConfigurationError(
                f"Unsupported instruction cache hint: {self.cache_hint!r}",
            )


@dataclass(frozen=True)
class ModelUsage:
    """Normalized token accounting returned by every backend."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class TextResult:
    """Provider-independent text generation result."""

    text: str
    usage: ModelUsage = field(default_factory=ModelUsage)
    model: str | None = None
    request_id: str | None = None


@dataclass(frozen=True)
class StructuredResult(Generic[StructuredT]):
    """Validated structured generation result."""

    parsed: StructuredT
    usage: ModelUsage = field(default_factory=ModelUsage)
    model: str | None = None
    request_id: str | None = None


@runtime_checkable
class ModelBackend(Protocol):
    """The only model-generation interface used by provider-neutral code."""

    provider_id: str

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
        """Generate free-form text."""

    def generate_structured(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        output_type: type[StructuredT],
        system: str | Sequence[InstructionPart] | None = None,
        max_tokens: int = 8192,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> StructuredResult[StructuredT]:
        """Generate and validate a value of ``output_type``."""
