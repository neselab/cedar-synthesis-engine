"""Registry and lazy factories for AutoCedar model backends."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable, Literal

from autocedar.providers.base import BackendUnavailableError, ModelBackend
from autocedar.providers.config import (
    DEFAULT_MODELS,
    PROVIDER_ALIASES,
    canonical_provider_id,
)


AuthMode = Literal["oauth", "cli", "api-key", "optional-api-key"]
BackendFactory = Callable[..., ModelBackend]


@dataclass(frozen=True)
class ProviderDefinition:
    """Human-facing metadata and a lazily imported backend factory."""

    provider_id: str
    display_name: str
    auth_mode: AuthMode
    default_model: str
    aliases: tuple[str, ...] = ()
    factory: str | BackendFactory = ""
    description: str = ""

    def __post_init__(self) -> None:
        canonical = canonical_provider_id(self.provider_id)
        if canonical != self.provider_id:
            raise ValueError(
                f"Provider definitions must use canonical IDs; use {canonical!r}.",
            )
        if not self.display_name.strip():
            raise ValueError("Provider display_name must not be empty.")
        if self.auth_mode not in {"oauth", "cli", "api-key", "optional-api-key"}:
            raise ValueError(f"Unsupported provider auth mode: {self.auth_mode!r}")
        if not self.default_model.strip():
            raise ValueError("Provider default_model must not be empty.")
        for alias in self.aliases:
            if canonical_provider_id(alias) != self.provider_id:
                raise ValueError(
                    f"Alias {alias!r} does not resolve to {self.provider_id!r}.",
                )
        if not self.factory:
            raise ValueError("Provider factory must be a callable or 'module:attribute' string.")
        if isinstance(self.factory, str) and ":" not in self.factory:
            raise ValueError("String provider factories must use 'module:attribute' syntax.")

    @property
    def requires_api_key(self) -> bool:
        return self.auth_mode == "api-key"


class ProviderRegistry:
    """Canonical provider lookup with imports deferred until backend creation."""

    def __init__(self, *definitions: ProviderDefinition) -> None:
        self._definitions: dict[str, ProviderDefinition] = {}
        self._names: dict[str, str] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: ProviderDefinition) -> None:
        if not isinstance(definition, ProviderDefinition):
            raise TypeError("definition must be a ProviderDefinition")
        if definition.provider_id in self._definitions:
            raise ValueError(f"Provider {definition.provider_id!r} is already registered.")
        names = (definition.provider_id, *definition.aliases)
        normalized_names = [name.strip().lower().replace("_", "-") for name in names]
        collisions = [name for name in normalized_names if name in self._names]
        if collisions:
            raise ValueError(f"Provider name already registered: {collisions[0]!r}.")
        self._definitions[definition.provider_id] = definition
        for name in normalized_names:
            self._names[name] = definition.provider_id

    def resolve(self, provider: str) -> ProviderDefinition:
        normalized = provider.strip().lower().replace("_", "-") if isinstance(provider, str) else ""
        canonical = self._names.get(normalized)
        if canonical is None:
            # Produce the shared, consistent unknown-provider diagnostic.
            canonical_provider_id(provider)
            raise AssertionError("canonical provider is absent from the registry")
        return self._definitions[canonical]

    def definitions(self) -> tuple[ProviderDefinition, ...]:
        return tuple(self._definitions[provider] for provider in self._definitions)

    def provider_ids(self) -> tuple[str, ...]:
        return tuple(self._definitions)

    def load_factory(self, provider: str) -> BackendFactory:
        definition = self.resolve(provider)
        if callable(definition.factory):
            return definition.factory
        module_name, attribute = definition.factory.split(":", 1)
        try:
            module = importlib.import_module(module_name)
            factory = getattr(module, attribute)
        except (ImportError, AttributeError) as exc:
            raise BackendUnavailableError(
                f"The {definition.display_name} backend is not available: {exc}",
            ) from exc
        if not callable(factory):
            raise BackendUnavailableError(
                f"The {definition.display_name} backend factory {definition.factory!r} "
                "is not callable.",
            )
        return factory

    def create(self, provider: str, **kwargs: Any) -> ModelBackend:
        definition = self.resolve(provider)
        factory = self.load_factory(provider)
        try:
            backend = factory(**kwargs)
        except BackendUnavailableError:
            raise
        except Exception as exc:
            raise BackendUnavailableError(
                f"Could not initialize the {definition.display_name} backend: {exc}",
            ) from exc
        if not isinstance(backend, ModelBackend):
            raise BackendUnavailableError(
                f"Factory for {definition.display_name} did not return a ModelBackend.",
            )
        return backend


DEFAULT_REGISTRY = ProviderRegistry(
    ProviderDefinition(
        provider_id="codex",
        display_name="OpenAI Codex",
        auth_mode="oauth",
        default_model=DEFAULT_MODELS["codex"],
        aliases=tuple(
            alias for alias, provider in PROVIDER_ALIASES.items()
            if provider == "codex" and alias != "codex"
        ),
        factory="autocedar.providers.codex_oauth:CodexOAuthBackend",
        description="Codex via the user's existing Codex OAuth login.",
    ),
    ProviderDefinition(
        provider_id="claude-cli",
        display_name="Claude CLI",
        auth_mode="cli",
        default_model=DEFAULT_MODELS["claude-cli"],
        aliases=tuple(
            alias for alias, provider in PROVIDER_ALIASES.items()
            if provider == "claude-cli" and alias != "claude-cli"
        ),
        factory="autocedar.providers.claude_cli:ClaudeCLIBackend",
        description="Claude through the locally authenticated `claude -p` command.",
    ),
    ProviderDefinition(
        provider_id="anthropic",
        display_name="Anthropic API",
        auth_mode="api-key",
        default_model=DEFAULT_MODELS["anthropic"],
        aliases=(),
        factory="autocedar.providers.anthropic_api:AnthropicAPIBackend",
        description="Claude through an Anthropic API key.",
    ),
    ProviderDefinition(
        provider_id="openai",
        display_name="OpenAI API",
        auth_mode="api-key",
        default_model=DEFAULT_MODELS["openai"],
        aliases=(),
        factory="autocedar.providers.openai_api:OpenAIAPIBackend",
        description="OpenAI models through an OpenAI platform API key.",
    ),
    ProviderDefinition(
        provider_id="local",
        display_name="Local OpenAI-compatible server",
        auth_mode="optional-api-key",
        default_model=DEFAULT_MODELS["local"],
        aliases=tuple(
            alias for alias, provider in PROVIDER_ALIASES.items()
            if provider == "local" and alias != "local"
        ),
        factory="autocedar.providers.local_openai:LocalOpenAIBackend",
        description="A local vLLM or other OpenAI-compatible endpoint.",
    ),
)


def get_provider_definition(provider: str) -> ProviderDefinition:
    return DEFAULT_REGISTRY.resolve(provider)


def create_backend(provider: str, **kwargs: Any) -> ModelBackend:
    return DEFAULT_REGISTRY.create(provider, **kwargs)


__all__ = [
    "AuthMode",
    "BackendFactory",
    "DEFAULT_REGISTRY",
    "ProviderDefinition",
    "ProviderRegistry",
    "create_backend",
    "get_provider_definition",
]
