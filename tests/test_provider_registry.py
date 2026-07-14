"""Focused tests for lazy provider registration and backend contracts."""

from __future__ import annotations

from typing import Sequence

import pytest
from pydantic import BaseModel

from autocedar.providers import (
    BackendUnavailableError,
    ChatMessage,
    DEFAULT_REGISTRY,
    ModelUsage,
    ProviderConfigurationError,
    ProviderDefinition,
    ProviderRegistry,
    StructuredResult,
    TextResult,
)
from autocedar.providers.base import InstructionPart


class ExampleOutput(BaseModel):
    answer: str


class FakeBackend:
    provider_id = "codex"

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
        return TextResult(text=f"{model}:{messages[0].content}", usage=ModelUsage(1, 2))

    def generate_structured(
        self,
        *,
        model: str,
        messages: Sequence[ChatMessage],
        output_type: type[ExampleOutput],
        system: str | Sequence[InstructionPart] | None = None,
        max_tokens: int = 8192,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> StructuredResult[ExampleOutput]:
        return StructuredResult(parsed=output_type(answer="ok"))


def test_default_registry_exposes_all_supported_provider_paths() -> None:
    assert DEFAULT_REGISTRY.provider_ids() == (
        "codex",
        "claude-cli",
        "anthropic",
        "openai",
        "local",
    )
    assert DEFAULT_REGISTRY.resolve("openai-codex").provider_id == "codex"
    assert DEFAULT_REGISTRY.resolve("claude-p").provider_id == "claude-cli"
    assert DEFAULT_REGISTRY.resolve("openai-compatible").provider_id == "local"
    assert DEFAULT_REGISTRY.resolve("openai").display_name == "OpenAI API"


def test_provider_metadata_reports_auth_modes() -> None:
    assert DEFAULT_REGISTRY.resolve("codex").auth_mode == "oauth"
    assert DEFAULT_REGISTRY.resolve("claude-cli").auth_mode == "cli"
    assert DEFAULT_REGISTRY.resolve("anthropic").requires_api_key is True
    assert DEFAULT_REGISTRY.resolve("openai").requires_api_key is True
    assert DEFAULT_REGISTRY.resolve("local").auth_mode == "optional-api-key"


def test_callable_factory_creates_model_backend() -> None:
    registry = ProviderRegistry(ProviderDefinition(
        provider_id="codex",
        display_name="Fake Codex",
        auth_mode="oauth",
        default_model="fake",
        aliases=("openai-codex",),
        factory=FakeBackend,
    ))

    backend = registry.create("openai-codex")
    result = backend.generate_text(
        model="fake",
        messages=[ChatMessage("user", "hello")],
    )

    assert result.text == "fake:hello"
    assert result.usage.total_tokens == 3


def test_lazy_factory_failure_is_actionable() -> None:
    registry = ProviderRegistry(ProviderDefinition(
        provider_id="anthropic",
        display_name="Missing Anthropic",
        auth_mode="api-key",
        default_model="fake",
        factory="autocedar.providers.does_not_exist:Backend",
    ))

    with pytest.raises(BackendUnavailableError, match="Missing Anthropic.*not available"):
        registry.create("anthropic")


def test_registry_rejects_duplicate_names() -> None:
    definition = ProviderDefinition(
        provider_id="codex",
        display_name="Codex",
        auth_mode="oauth",
        default_model="fake",
        aliases=("openai-codex",),
        factory=FakeBackend,
    )
    registry = ProviderRegistry(definition)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(definition)


def test_unknown_provider_error_lists_canonical_choices() -> None:
    with pytest.raises(ProviderConfigurationError, match="codex.*claude-cli.*anthropic"):
        DEFAULT_REGISTRY.resolve("mystery-provider")


def test_contract_validates_messages_and_instruction_cache_hints() -> None:
    with pytest.raises(ProviderConfigurationError, match="Message content"):
        ChatMessage("user", "")
    with pytest.raises(ProviderConfigurationError, match="cache hint"):
        InstructionPart("stable context", "forever")  # type: ignore[arg-type]
