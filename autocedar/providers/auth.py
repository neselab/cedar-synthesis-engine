"""Provider-scoped credential storage with private atomic files."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

from autocedar.providers.base import ProviderConfigurationError
from autocedar.providers.config import (
    CONFIG_VERSION,
    _atomic_write_private_json,
    _clean,
    _read_legacy_env,
    _read_private_json,
    _reject_unknown_keys,
    canonical_provider_id,
    config_directory,
)


_API_KEY_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "codex": (),
    "claude-cli": (),
    "anthropic": ("ANTHROPIC_API_KEY", "AUTOCEDAR_ANTHROPIC_API_KEY"),
    "openai": ("OPENAI_API_KEY",),
    "local": ("AUTOCEDAR_LOCAL_API_KEY", "AUTOCEDAR_OPENAI_API_KEY"),
}

MIGRATED_AUTH_ENV_KEYS = frozenset(
    key for keys in _API_KEY_ENV_KEYS.values() for key in keys
)


def auth_path(environ: Mapping[str, str] | None = None) -> Path:
    return config_directory(environ) / "auth.json"


@dataclass(frozen=True, repr=False)
class ProviderCredential:
    """A provider API key whose representation is always redacted."""

    api_key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "api_key", _validate_api_key(self.api_key))

    def __repr__(self) -> str:
        return "ProviderCredential(api_key='[redacted]')"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProviderCredential":
        _reject_unknown_keys(payload, {"api_key"}, "provider credential")
        api_key = payload.get("api_key")
        if not isinstance(api_key, str):
            raise ProviderConfigurationError("provider credential api_key must be a string.")
        return cls(api_key=api_key)


@dataclass(frozen=True, repr=False)
class ProviderAuth:
    """Versioned contents of ``auth.json``."""

    providers: Mapping[str, ProviderCredential] = field(default_factory=dict)
    legacy_env_migrated: bool = False
    version: int = CONFIG_VERSION

    def __post_init__(self) -> None:
        if self.version != CONFIG_VERSION:
            raise ProviderConfigurationError(
                f"Unsupported auth version {self.version!r}; expected {CONFIG_VERSION}.",
            )
        if not isinstance(self.legacy_env_migrated, bool):
            raise ProviderConfigurationError("auth.legacy_env_migrated must be a boolean.")
        normalized: dict[str, ProviderCredential] = {}
        for raw_provider, credential in self.providers.items():
            provider = canonical_provider_id(raw_provider)
            if provider in normalized:
                raise ProviderConfigurationError(
                    f"Credential for {provider!r} appears more than once.",
                )
            if not isinstance(credential, ProviderCredential):
                raise ProviderConfigurationError(
                    f"Credential for {raw_provider!r} must be ProviderCredential.",
                )
            normalized[provider] = credential
        object.__setattr__(self, "providers", normalized)

    def __repr__(self) -> str:
        providers = ", ".join(sorted(self.providers))
        return (
            "ProviderAuth("
            f"providers=[{providers}], "
            f"legacy_env_migrated={self.legacy_env_migrated}, "
            f"version={self.version})"
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProviderAuth":
        _reject_unknown_keys(
            payload,
            {"version", "providers", "legacy_env_migrated"},
            "auth",
        )
        version = payload.get("version", CONFIG_VERSION)
        if not isinstance(version, int) or isinstance(version, bool):
            raise ProviderConfigurationError("auth.version must be an integer.")
        legacy_env_migrated = payload.get("legacy_env_migrated", False)
        if not isinstance(legacy_env_migrated, bool):
            raise ProviderConfigurationError("auth.legacy_env_migrated must be a boolean.")
        raw_providers = payload.get("providers", {})
        if not isinstance(raw_providers, Mapping):
            raise ProviderConfigurationError("auth.providers must be an object.")
        providers: dict[str, ProviderCredential] = {}
        for raw_provider, raw_credential in raw_providers.items():
            if not isinstance(raw_provider, str) or not isinstance(raw_credential, Mapping):
                raise ProviderConfigurationError(
                    "Each auth.providers entry must map a provider name to an object.",
                )
            provider = canonical_provider_id(raw_provider)
            if provider in providers:
                raise ProviderConfigurationError(
                    f"Credential for {provider!r} appears more than once.",
                )
            providers[provider] = ProviderCredential.from_dict(raw_credential)
        return cls(
            providers=providers,
            legacy_env_migrated=legacy_env_migrated,
            version=version,
        )

    def get_api_key(self, provider: str) -> str | None:
        credential = self.providers.get(canonical_provider_id(provider))
        return credential.api_key if credential is not None else None

    def with_api_key(self, provider: str, api_key: str) -> "ProviderAuth":
        canonical = canonical_provider_id(provider)
        updated = dict(self.providers)
        updated[canonical] = ProviderCredential(api_key=api_key)
        return replace(self, providers=updated)

    def without_api_key(self, provider: str) -> "ProviderAuth":
        canonical = canonical_provider_id(provider)
        updated = dict(self.providers)
        updated.pop(canonical, None)
        return replace(self, providers=updated)

    def to_redacted_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "legacy_env_migrated": self.legacy_env_migrated,
            "providers": {
                provider: {"api_key": "[redacted]"}
                for provider in sorted(self.providers)
            },
        }

    def _to_storage_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "legacy_env_migrated": self.legacy_env_migrated,
            "providers": {
                provider: {"api_key": self.providers[provider].api_key}
                for provider in sorted(self.providers)
            },
        }


@dataclass(frozen=True, repr=False)
class ResolvedCredential:
    """An effective key and its precedence source, with a redacted repr."""

    api_key: str | None
    source: str

    def __repr__(self) -> str:
        rendered = "[set]" if self.api_key else "[unset]"
        return f"ResolvedCredential(api_key={rendered!r}, source={self.source!r})"


class AuthStore:
    """Read and atomically write a private provider-scoped ``auth.json``."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = (path or auth_path()).expanduser()

    @property
    def legacy_path(self) -> Path:
        return self.path.parent / ".env"

    def load(self, *, migrate_legacy: bool = True) -> ProviderAuth:
        if self.path.exists():
            auth = ProviderAuth.from_dict(_read_private_json(self.path))
        else:
            auth = ProviderAuth()
        if (
            not migrate_legacy
            or auth.legacy_env_migrated
            or not self.legacy_path.exists()
        ):
            return auth
        migrated = _merge_legacy_auth(auth, _read_legacy_env(self.legacy_path))
        migrated = replace(migrated, legacy_env_migrated=True)
        self.save(migrated)
        return migrated

    def save(self, auth: ProviderAuth) -> Path:
        if not isinstance(auth, ProviderAuth):
            raise TypeError("auth must be a ProviderAuth instance")
        _atomic_write_private_json(self.path, auth._to_storage_dict())
        return self.path

    def get_api_key(self, provider: str) -> str | None:
        return self.load().get_api_key(provider)

    def set_api_key(self, provider: str, api_key: str) -> ProviderAuth:
        auth = self.load().with_api_key(provider, api_key)
        self.save(auth)
        return auth

    def remove_api_key(self, provider: str) -> ProviderAuth:
        auth = self.load().without_api_key(provider)
        self.save(auth)
        return auth


def resolve_api_key(
    provider: str,
    *,
    session_api_key: str | None = None,
    environ: Mapping[str, str] | None = None,
    auth: ProviderAuth | None = None,
) -> ResolvedCredential:
    """Resolve ``session > environment/project .env > auth.json`` credentials."""

    canonical = canonical_provider_id(provider)
    env = os.environ if environ is None else environ
    session_value = _clean(session_api_key)
    if session_value:
        return ResolvedCredential(_validate_api_key(session_value), "session")
    for key in _API_KEY_ENV_KEYS[canonical]:
        value = _clean(env.get(key))
        if value:
            return ResolvedCredential(_validate_api_key(value), f"environment:{key}")
    saved = auth if auth is not None else AuthStore().load()
    value = saved.get_api_key(canonical)
    if value:
        return ResolvedCredential(value, f"auth:providers.{canonical}.api_key")
    return ResolvedCredential(None, "unset")


def _merge_legacy_auth(auth: ProviderAuth, legacy: Mapping[str, str]) -> ProviderAuth:
    result = auth
    for provider, keys in _API_KEY_ENV_KEYS.items():
        if result.get_api_key(provider):
            continue
        for key in keys:
            value = _clean(legacy.get(key))
            if value:
                try:
                    result = result.with_api_key(provider, value)
                except ProviderConfigurationError:
                    # Older example files commonly contain placeholders. They
                    # should not poison first-run migration or become secrets.
                    continue
                break
    return result


def _validate_api_key(value: str) -> str:
    if not isinstance(value, str):
        raise ProviderConfigurationError("API key must be a string.")
    key = value.strip().strip("\"'")
    if not key:
        raise ProviderConfigurationError("API key must not be empty.")
    if len(key) > 65536 or any(character in key for character in "\r\n\0"):
        raise ProviderConfigurationError("API key contains invalid characters.")
    placeholders = {
        "your-api-key",
        "your-anthropic-api-key",
        "your-openai-api-key",
        "sk-ant-...",
        "sk-...",
        "[redacted]",
        "redacted",
    }
    if key.lower() in placeholders:
        raise ProviderConfigurationError("Refusing to save a placeholder or redacted API key.")
    return key


__all__ = [
    "AuthStore",
    "ProviderAuth",
    "ProviderCredential",
    "ResolvedCredential",
    "auth_path",
    "resolve_api_key",
]
