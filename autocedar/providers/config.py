"""Persistent, non-secret provider settings and precedence resolution."""

from __future__ import annotations

import json
import os
import shlex
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from autocedar.providers.base import ProviderConfigurationError


CONFIG_VERSION = 1
USER_CONFIG_DIR_ENV = "AUTOCEDAR_CONFIG_DIR"
CANONICAL_PROVIDER_IDS = ("codex", "claude-cli", "anthropic", "openai", "local")
PROVIDER_ALIASES: dict[str, str] = {
    "codex": "codex",
    "openai-codex": "codex",
    "claude-cli": "claude-cli",
    "claude-code": "claude-cli",
    "claude-p": "claude-cli",
    "anthropic": "anthropic",
    "openai": "openai",
    "local": "local",
    "vllm": "local",
    "openai-compatible": "local",
}
REASONING_EFFORTS = ("low", "medium", "high", "max")
DEFAULT_MODELS: dict[str, str] = {
    "codex": "gpt-5.5",
    "claude-cli": "sonnet",
    "anthropic": "claude-opus-4-7",
    "openai": "gpt-5.6",
    "local": "autocedar-local",
}
DEFAULT_LOCAL_BASE_URL = "http://127.0.0.1:8000/v1"

_MODEL_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "codex": ("AUTOCEDAR_CODEX_MODEL",),
    "claude-cli": ("AUTOCEDAR_CLAUDE_CLI_MODEL", "AUTOCEDAR_CLAUDE_MODEL"),
    "anthropic": ("AUTOCEDAR_ANTHROPIC_MODEL",),
    "openai": ("AUTOCEDAR_OPENAI_MODEL",),
    "local": ("AUTOCEDAR_LOCAL_MODEL",),
}
_GENERIC_MODEL_ENV_KEYS = (
    "AUTOCEDAR_MODEL",
    "AUTOCEDAR_AUTHOR_MODEL",
    "AUTOCEDAR_CHAT_MODEL",
)
_BASE_URL_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "openai": ("AUTOCEDAR_OPENAI_BASE_URL",),
    "local": ("AUTOCEDAR_LOCAL_BASE_URL",),
}

# Before direct OpenAI API support existed, these ``OPENAI``-named variables
# configured the local OpenAI-compatible transport. They are intentionally not
# runtime aliases anymore: otherwise selecting ``local`` can silently inherit
# cloud OpenAI configuration. The one-time legacy migration below still
# recognizes them when the legacy file explicitly selects the local provider.
_LEGACY_LOCAL_MODEL_ENV_KEYS = ("AUTOCEDAR_OPENAI_MODEL",)
_LEGACY_LOCAL_BASE_URL_ENV_KEYS = ("AUTOCEDAR_OPENAI_BASE_URL",)

MIGRATED_SETTINGS_ENV_KEYS = frozenset({
    "AUTOCEDAR_PROVIDER",
    "AUTOCEDAR_EFFORT",
    *_GENERIC_MODEL_ENV_KEYS,
    *(key for keys in _MODEL_ENV_KEYS.values() for key in keys),
    *(key for keys in _BASE_URL_ENV_KEYS.values() for key in keys),
    *_LEGACY_LOCAL_MODEL_ENV_KEYS,
    *_LEGACY_LOCAL_BASE_URL_ENV_KEYS,
})


def canonical_provider_id(value: str) -> str:
    """Return the canonical provider ID for a public name or alias."""

    if not isinstance(value, str):
        raise ProviderConfigurationError("Provider ID must be a string.")
    normalized = value.strip().lower().replace("_", "-")
    canonical = PROVIDER_ALIASES.get(normalized)
    if canonical is None:
        accepted = ", ".join(CANONICAL_PROVIDER_IDS)
        raise ProviderConfigurationError(
            f"Unknown provider {value!r}. Expected one of: {accepted}.",
        )
    return canonical


def config_directory(environ: Mapping[str, str] | None = None) -> Path:
    """Return AutoCedar's user configuration directory."""

    env = os.environ if environ is None else environ
    explicit = _clean(env.get(USER_CONFIG_DIR_ENV))
    if explicit:
        return Path(explicit).expanduser()
    xdg = _clean(env.get("XDG_CONFIG_HOME"))
    if xdg:
        return Path(xdg).expanduser() / "autocedar"
    return Path.home() / ".config" / "autocedar"


def settings_path(environ: Mapping[str, str] | None = None) -> Path:
    return config_directory(environ) / "settings.json"


def legacy_env_path(environ: Mapping[str, str] | None = None) -> Path:
    return config_directory(environ) / ".env"


@dataclass(frozen=True)
class ProviderOptions:
    """Saved non-secret options for one provider."""

    model: str | None = None
    base_url: str | None = None
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        if self.model is not None:
            object.__setattr__(self, "model", _validate_model(self.model))
        if self.base_url is not None:
            object.__setattr__(self, "base_url", _validate_base_url(self.base_url))
        if self.reasoning_effort is not None:
            object.__setattr__(
                self,
                "reasoning_effort",
                _validate_reasoning_effort(self.reasoning_effort),
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProviderOptions":
        _reject_unknown_keys(
            payload,
            {"model", "base_url", "reasoning_effort"},
            "provider settings",
        )
        return cls(
            model=_optional_string(payload.get("model"), "model"),
            base_url=_optional_string(payload.get("base_url"), "base_url"),
            reasoning_effort=_optional_string(
                payload.get("reasoning_effort"),
                "reasoning_effort",
            ),
        )

    def to_dict(self) -> dict[str, str]:
        result: dict[str, str] = {}
        if self.model is not None:
            result["model"] = self.model
        if self.base_url is not None:
            result["base_url"] = self.base_url
        if self.reasoning_effort is not None:
            result["reasoning_effort"] = self.reasoning_effort
        return result


@dataclass(frozen=True)
class ProviderSettings:
    """Versioned contents of ``settings.json`` (never credentials)."""

    default_provider: str = "codex"
    providers: Mapping[str, ProviderOptions] = field(default_factory=dict)
    legacy_env_migrated: bool = False
    version: int = CONFIG_VERSION

    def __post_init__(self) -> None:
        if self.version != CONFIG_VERSION:
            raise ProviderConfigurationError(
                f"Unsupported settings version {self.version!r}; expected {CONFIG_VERSION}.",
            )
        if not isinstance(self.legacy_env_migrated, bool):
            raise ProviderConfigurationError("settings.legacy_env_migrated must be a boolean.")
        object.__setattr__(self, "default_provider", canonical_provider_id(self.default_provider))
        normalized: dict[str, ProviderOptions] = {}
        for raw_provider, raw_options in self.providers.items():
            provider = canonical_provider_id(raw_provider)
            if provider in normalized:
                raise ProviderConfigurationError(
                    f"Provider {provider!r} appears more than once (possibly through an alias).",
                )
            if not isinstance(raw_options, ProviderOptions):
                raise ProviderConfigurationError(
                    f"Settings for {raw_provider!r} must be ProviderOptions.",
                )
            normalized[provider] = raw_options
        object.__setattr__(self, "providers", normalized)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProviderSettings":
        _reject_unknown_keys(
            payload,
            {"version", "default_provider", "providers", "legacy_env_migrated"},
            "settings",
        )
        version = payload.get("version", CONFIG_VERSION)
        if not isinstance(version, int) or isinstance(version, bool):
            raise ProviderConfigurationError("settings.version must be an integer.")
        default_provider = payload.get("default_provider", "codex")
        if not isinstance(default_provider, str):
            raise ProviderConfigurationError("settings.default_provider must be a string.")
        legacy_env_migrated = payload.get("legacy_env_migrated", False)
        if not isinstance(legacy_env_migrated, bool):
            raise ProviderConfigurationError("settings.legacy_env_migrated must be a boolean.")
        raw_providers = payload.get("providers", {})
        if not isinstance(raw_providers, Mapping):
            raise ProviderConfigurationError("settings.providers must be an object.")
        providers: dict[str, ProviderOptions] = {}
        for raw_provider, raw_options in raw_providers.items():
            if not isinstance(raw_provider, str) or not isinstance(raw_options, Mapping):
                raise ProviderConfigurationError(
                    "Each settings.providers entry must map a provider name to an object.",
                )
            canonical = canonical_provider_id(raw_provider)
            if canonical in providers:
                raise ProviderConfigurationError(
                    f"Provider {canonical!r} appears more than once (possibly through an alias).",
                )
            providers[canonical] = ProviderOptions.from_dict(raw_options)
        return cls(
            version=version,
            default_provider=default_provider,
            providers=providers,
            legacy_env_migrated=legacy_env_migrated,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "default_provider": self.default_provider,
            "legacy_env_migrated": self.legacy_env_migrated,
            "providers": {
                provider: self.providers[provider].to_dict()
                for provider in sorted(self.providers)
            },
        }

    def options_for(self, provider: str) -> ProviderOptions:
        return self.providers.get(canonical_provider_id(provider), ProviderOptions())

    def with_default_provider(self, provider: str) -> "ProviderSettings":
        return replace(self, default_provider=canonical_provider_id(provider))

    def with_provider_options(
        self,
        provider: str,
        options: ProviderOptions,
    ) -> "ProviderSettings":
        canonical = canonical_provider_id(provider)
        updated = dict(self.providers)
        updated[canonical] = options
        return replace(self, providers=updated)


@dataclass(frozen=True)
class SessionOverrides:
    """Non-persistent choices made in the current CLI/TUI session."""

    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    reasoning_effort: str | None = None


@dataclass(frozen=True)
class ResolvedProviderConfig:
    """Effective provider settings plus a source label for every field."""

    provider: str
    model: str
    base_url: str | None
    reasoning_effort: str | None
    sources: Mapping[str, str]

    def source_for(self, field_name: str) -> str:
        try:
            return self.sources[field_name]
        except KeyError as exc:
            raise KeyError(f"Unknown resolved provider field: {field_name}") from exc


class SettingsStore:
    """Read and atomically write a private ``settings.json`` file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = (path or settings_path()).expanduser()

    @property
    def legacy_path(self) -> Path:
        return self.path.parent / ".env"

    def load(self, *, migrate_legacy: bool = True) -> ProviderSettings:
        existed = self.path.exists()
        if existed:
            payload = _read_private_json(self.path)
            settings = ProviderSettings.from_dict(payload)
        else:
            settings = ProviderSettings()
        if (
            not migrate_legacy
            or settings.legacy_env_migrated
            or not self.legacy_path.exists()
        ):
            return settings
        migrated, _ = _merge_legacy_settings(
            settings,
            _read_legacy_env(self.legacy_path),
            allow_default_provider=not existed,
        )
        migrated = replace(migrated, legacy_env_migrated=True)
        self.save(migrated)
        return migrated

    def save(self, settings: ProviderSettings) -> Path:
        if not isinstance(settings, ProviderSettings):
            raise TypeError("settings must be a ProviderSettings instance")
        _atomic_write_private_json(self.path, settings.to_dict())
        return self.path

    def set_default_provider(self, provider: str) -> ProviderSettings:
        settings = self.load().with_default_provider(provider)
        self.save(settings)
        return settings

    def set_provider_options(
        self,
        provider: str,
        options: ProviderOptions,
    ) -> ProviderSettings:
        settings = self.load().with_provider_options(provider, options)
        self.save(settings)
        return settings


def resolve_provider_config(
    *,
    session: SessionOverrides | Mapping[str, str | None] | None = None,
    environ: Mapping[str, str] | None = None,
    settings: ProviderSettings | None = None,
    defaults: Mapping[str, ProviderOptions] | None = None,
) -> ResolvedProviderConfig:
    """Resolve ``session > environment > settings.json > defaults``.

    Project ``.env`` values participate through ``environ`` after the existing
    AutoCedar dotenv loader has populated the process environment. Tests and
    embedders can pass an isolated mapping instead.
    """

    env = os.environ if environ is None else environ
    saved = settings if settings is not None else SettingsStore().load()
    current = _coerce_session(session)
    fallback = dict(_default_provider_options())
    if defaults is not None:
        for raw_provider, options in defaults.items():
            provider = canonical_provider_id(raw_provider)
            if not isinstance(options, ProviderOptions):
                raise TypeError("defaults values must be ProviderOptions instances")
            fallback[provider] = options

    provider_raw, provider_source = _first_value(
        (current.provider, "session"),
        (env.get("AUTOCEDAR_PROVIDER"), "environment:AUTOCEDAR_PROVIDER"),
        (saved.default_provider, "settings:default_provider"),
        ("codex", "default"),
    )
    provider = canonical_provider_id(provider_raw)
    saved_options = saved.options_for(provider)
    default_options = fallback[provider]

    model_candidates: list[tuple[str | None, str]] = [(current.model, "session")]
    model_candidates.extend(
        (env.get(key), f"environment:{key}") for key in _MODEL_ENV_KEYS[provider]
    )
    model_candidates.extend(
        (env.get(key), f"environment:{key}") for key in _GENERIC_MODEL_ENV_KEYS
    )
    model_candidates.extend([
        (saved_options.model, f"settings:providers.{provider}.model"),
        (default_options.model, f"default:{provider}.model"),
    ])
    model_raw, model_source = _first_value(*model_candidates)
    model = _validate_model(model_raw)

    base_candidates: list[tuple[str | None, str]] = [(current.base_url, "session")]
    base_candidates.extend(
        (env.get(key), f"environment:{key}") for key in _BASE_URL_ENV_KEYS.get(provider, ())
    )
    base_candidates.extend([
        (saved_options.base_url, f"settings:providers.{provider}.base_url"),
        (default_options.base_url, f"default:{provider}.base_url"),
    ])
    base_raw, base_source = _first_optional_value(*base_candidates)
    base_url = _validate_base_url(base_raw) if base_raw is not None else None

    effort_raw, effort_source = _first_optional_value(
        (current.reasoning_effort, "session"),
        (env.get("AUTOCEDAR_EFFORT"), "environment:AUTOCEDAR_EFFORT"),
        (
            saved_options.reasoning_effort,
            f"settings:providers.{provider}.reasoning_effort",
        ),
        (
            default_options.reasoning_effort,
            f"default:{provider}.reasoning_effort",
        ),
    )
    effort = _validate_reasoning_effort(effort_raw) if effort_raw is not None else None

    return ResolvedProviderConfig(
        provider=provider,
        model=model,
        base_url=base_url,
        reasoning_effort=effort,
        sources={
            "provider": provider_source,
            "model": model_source,
            "base_url": base_source,
            "reasoning_effort": effort_source,
        },
    )


def _default_provider_options() -> dict[str, ProviderOptions]:
    return {
        provider: ProviderOptions(
            model=model,
            base_url=DEFAULT_LOCAL_BASE_URL if provider == "local" else None,
            reasoning_effort="high" if provider == "codex" else None,
        )
        for provider, model in DEFAULT_MODELS.items()
    }


def _coerce_session(
    session: SessionOverrides | Mapping[str, str | None] | None,
) -> SessionOverrides:
    if session is None:
        return SessionOverrides()
    if isinstance(session, SessionOverrides):
        return session
    if not isinstance(session, Mapping):
        raise TypeError("session must be SessionOverrides or a mapping")
    allowed = {"provider", "model", "base_url", "reasoning_effort"}
    _reject_unknown_keys(session, allowed, "session overrides")
    return SessionOverrides(
        provider=session.get("provider"),
        model=session.get("model"),
        base_url=session.get("base_url"),
        reasoning_effort=session.get("reasoning_effort"),
    )


def _merge_legacy_settings(
    settings: ProviderSettings,
    legacy: Mapping[str, str],
    *,
    allow_default_provider: bool,
) -> tuple[ProviderSettings, bool]:
    changed = False
    result = settings
    selected = settings.default_provider
    legacy_provider = _clean(legacy.get("AUTOCEDAR_PROVIDER"))
    if allow_default_provider and legacy_provider:
        selected = canonical_provider_id(legacy_provider)
        if selected != result.default_provider:
            result = result.with_default_provider(selected)
            changed = True

    for provider in CANONICAL_PROVIDER_IDS:
        existing = result.options_for(provider)
        model = existing.model
        base_url = existing.base_url
        effort = existing.reasoning_effort
        if model is None:
            model_keys = _MODEL_ENV_KEYS[provider]
            if provider == "local" and selected == "local":
                model_keys += _LEGACY_LOCAL_MODEL_ENV_KEYS
            # With an explicitly selected legacy local provider, the old
            # OPENAI-named values belong only to local, not the new direct API.
            if provider == "openai" and selected == "local":
                model_keys = tuple(
                    key for key in model_keys
                    if key not in _LEGACY_LOCAL_MODEL_ENV_KEYS
                )
            for key in model_keys:
                candidate = _clean(legacy.get(key))
                if candidate:
                    model = candidate
                    break
        if model is None and provider == selected:
            for key in _GENERIC_MODEL_ENV_KEYS:
                candidate = _clean(legacy.get(key))
                if candidate:
                    model = candidate
                    break
        if base_url is None:
            base_url_keys = _BASE_URL_ENV_KEYS.get(provider, ())
            if provider == "local" and selected == "local":
                base_url_keys += _LEGACY_LOCAL_BASE_URL_ENV_KEYS
            if provider == "openai" and selected == "local":
                base_url_keys = tuple(
                    key for key in base_url_keys
                    if key not in _LEGACY_LOCAL_BASE_URL_ENV_KEYS
                )
            for key in base_url_keys:
                candidate = _clean(legacy.get(key))
                if candidate:
                    base_url = candidate
                    break
        if effort is None and provider == selected:
            effort = _clean(legacy.get("AUTOCEDAR_EFFORT"))
        migrated = ProviderOptions(
            model=model or None,
            base_url=base_url or None,
            reasoning_effort=effort or None,
        )
        if migrated != existing and any(migrated.to_dict().values()):
            result = result.with_provider_options(provider, migrated)
            changed = True
    return result, changed


def _read_legacy_env(path: Path) -> dict[str, str]:
    """Read the legacy user ``.env`` without mutating or deleting it."""

    values: dict[str, str] = {}
    try:
        _secure_config_directory(path.parent)
        os.chmod(path, 0o600)
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ProviderConfigurationError(f"Could not read legacy config {path}: {exc}") from exc
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        try:
            parsed = shlex.split(raw_value.strip(), comments=True, posix=True)
        except ValueError:
            parsed = [raw_value.strip().strip("\"'")]
        values[key] = parsed[0] if parsed else ""
    return values


def _read_private_json(path: Path) -> Mapping[str, Any]:
    _secure_config_directory(path.parent)
    try:
        os.chmod(path, 0o600)
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProviderConfigurationError(
            f"Invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}",
        ) from exc
    except OSError as exc:
        raise ProviderConfigurationError(f"Could not read {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ProviderConfigurationError(f"{path} must contain a JSON object.")
    return payload


def _atomic_write_private_json(path: Path, payload: Mapping[str, Any]) -> None:
    _secure_config_directory(path.parent)
    try:
        contents = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    except (TypeError, ValueError) as exc:
        raise ProviderConfigurationError(f"Could not serialize configuration: {exc}") from exc
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            fd = -1
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        _fsync_directory(path.parent)
    except OSError as exc:
        raise ProviderConfigurationError(f"Could not write {path}: {exc}") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        temporary.unlink(missing_ok=True)


def _secure_config_directory(path: Path) -> None:
    try:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path, 0o700)
    except OSError as exc:
        raise ProviderConfigurationError(
            f"Could not secure config directory {path}: {exc}",
        ) from exc


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _validate_model(value: str) -> str:
    model = _clean(value)
    if not model:
        raise ProviderConfigurationError("Model name must be a non-empty string.")
    if len(model) > 512 or any(character in model for character in "\r\n\0"):
        raise ProviderConfigurationError("Model name contains invalid characters.")
    return model


def _validate_base_url(value: str) -> str:
    base_url = _clean(value)
    if not base_url:
        raise ProviderConfigurationError("Base URL must be a non-empty string.")
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ProviderConfigurationError("Base URL must be an absolute http:// or https:// URL.")
    if parsed.username is not None or parsed.password is not None:
        raise ProviderConfigurationError(
            "Base URL must not contain credentials; save an API key in auth.json instead.",
        )
    if parsed.query or parsed.fragment:
        raise ProviderConfigurationError("Base URL must not contain a query string or fragment.")
    return base_url.rstrip("/")


def _validate_reasoning_effort(value: str) -> str:
    effort = _clean(value).lower()
    if effort not in REASONING_EFFORTS:
        accepted = ", ".join(REASONING_EFFORTS)
        raise ProviderConfigurationError(f"Reasoning effort must be one of: {accepted}.")
    return effort


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProviderConfigurationError(f"{field_name} must be a string or null.")
    return value


def _reject_unknown_keys(
    payload: Mapping[str, Any],
    allowed: set[str],
    context: str,
) -> None:
    unknown = sorted(str(key) for key in payload if key not in allowed)
    if unknown:
        raise ProviderConfigurationError(
            f"Unknown {context} field(s): {', '.join(unknown)}.",
        )


def _first_value(*candidates: tuple[str | None, str]) -> tuple[str, str]:
    value, source = _first_optional_value(*candidates)
    if value is None:
        raise ProviderConfigurationError("No value or fallback was configured.")
    return value, source


def _first_optional_value(*candidates: tuple[str | None, str]) -> tuple[str | None, str]:
    for raw_value, source in candidates:
        value = _clean(raw_value)
        if value:
            return value, source
    return None, "unset"


def _clean(value: str | None) -> str:
    return value.strip() if isinstance(value, str) else ""


__all__ = [
    "CANONICAL_PROVIDER_IDS",
    "CONFIG_VERSION",
    "DEFAULT_LOCAL_BASE_URL",
    "DEFAULT_MODELS",
    "PROVIDER_ALIASES",
    "ProviderOptions",
    "ProviderSettings",
    "REASONING_EFFORTS",
    "ResolvedProviderConfig",
    "SessionOverrides",
    "SettingsStore",
    "canonical_provider_id",
    "config_directory",
    "legacy_env_path",
    "resolve_provider_config",
    "settings_path",
]
