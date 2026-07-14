"""Focused tests for provider settings and credential persistence."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from autocedar.providers import (
    AuthStore,
    ProviderAuth,
    ProviderConfigurationError,
    ProviderCredential,
    ProviderOptions,
    ProviderSettings,
    SessionOverrides,
    SettingsStore,
    canonical_provider_id,
    resolve_api_key,
    resolve_provider_config,
)


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("codex", "codex"),
        ("openai-codex", "codex"),
        ("claude-code", "claude-cli"),
        ("claude-p", "claude-cli"),
        ("anthropic", "anthropic"),
        ("openai", "openai"),
        ("vllm", "local"),
        ("openai_compatible", "local"),
    ],
)
def test_provider_aliases_are_canonicalized(alias: str, canonical: str) -> None:
    assert canonical_provider_id(alias) == canonical


def test_openai_api_and_codex_oauth_are_distinct_providers() -> None:
    assert canonical_provider_id("openai") == "openai"
    assert canonical_provider_id("openai-codex") == "codex"


def test_settings_round_trip_is_private_and_contains_no_credentials(tmp_path: Path) -> None:
    path = tmp_path / "config" / "settings.json"
    store = SettingsStore(path)
    settings = ProviderSettings(
        default_provider="local",
        providers={
            "local": ProviderOptions(
                model="Qwen/Qwen3-32B",
                base_url="http://jarvis:8000/v1/",
                reasoning_effort="medium",
            ),
        },
    )
    previous_umask = os.umask(0o022)
    try:
        store.save(settings)
    finally:
        os.umask(previous_umask)

    loaded = store.load(migrate_legacy=False)
    payload = path.read_text()

    assert loaded == settings
    assert loaded.options_for("vllm").base_url == "http://jarvis:8000/v1"
    assert "api_key" not in payload.lower()
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_config_precedence_and_source_reporting() -> None:
    settings = ProviderSettings(
        default_provider="anthropic",
        providers={
            "anthropic": ProviderOptions(model="saved-claude", reasoning_effort="low"),
            "local": ProviderOptions(
                model="saved-local",
                base_url="http://saved:8000/v1",
            ),
        },
    )
    environment = {
        "AUTOCEDAR_PROVIDER": "vllm",
        "AUTOCEDAR_LOCAL_MODEL": "env-local",
        "AUTOCEDAR_LOCAL_BASE_URL": "http://env:8000/v1",
        "AUTOCEDAR_EFFORT": "medium",
    }

    resolved = resolve_provider_config(
        settings=settings,
        environ=environment,
        session=SessionOverrides(model="session-local", reasoning_effort="max"),
    )

    assert resolved.provider == "local"
    assert resolved.model == "session-local"
    assert resolved.base_url == "http://env:8000/v1"
    assert resolved.reasoning_effort == "max"
    assert resolved.source_for("provider") == "environment:AUTOCEDAR_PROVIDER"
    assert resolved.source_for("model") == "session"
    assert resolved.source_for("base_url") == "environment:AUTOCEDAR_LOCAL_BASE_URL"
    assert resolved.source_for("reasoning_effort") == "session"


def test_project_environment_layer_beats_saved_json() -> None:
    settings = ProviderSettings(
        default_provider="openai",
        providers={"openai": ProviderOptions(model="saved-openai")},
    )

    resolved = resolve_provider_config(
        settings=settings,
        environ={
            "AUTOCEDAR_OPENAI_MODEL": "project-openai",
            "AUTOCEDAR_OPENAI_BASE_URL": "https://api.example.test/v1",
        },
    )

    assert resolved.provider == "openai"
    assert resolved.model == "project-openai"
    assert resolved.base_url == "https://api.example.test/v1"
    assert resolved.source_for("model") == "environment:AUTOCEDAR_OPENAI_MODEL"
    assert resolved.source_for("base_url") == "environment:AUTOCEDAR_OPENAI_BASE_URL"


def test_direct_openai_environment_does_not_leak_into_local_provider() -> None:
    settings = ProviderSettings(
        default_provider="local",
        providers={
            "local": ProviderOptions(
                model="saved-local",
                base_url="http://saved-local:8000/v1",
            ),
        },
    )

    resolved = resolve_provider_config(
        settings=settings,
        environ={
            "AUTOCEDAR_OPENAI_MODEL": "gpt-cloud",
            "AUTOCEDAR_OPENAI_BASE_URL": "https://api.openai.example/v1",
        },
    )

    assert resolved.provider == "local"
    assert resolved.model == "saved-local"
    assert resolved.base_url == "http://saved-local:8000/v1"
    assert resolved.source_for("model") == "settings:providers.local.model"
    assert resolved.source_for("base_url") == "settings:providers.local.base_url"


def test_base_url_rejects_embedded_credentials() -> None:
    with pytest.raises(ProviderConfigurationError, match="must not contain credentials"):
        ProviderOptions(base_url="https://secret@example.test/v1")


def test_settings_reject_credentials_and_unknown_fields() -> None:
    with pytest.raises(ProviderConfigurationError, match="Unknown provider settings"):
        ProviderSettings.from_dict({
            "providers": {"openai": {"model": "gpt", "api_key": "should-not-be-here"}},
        })


def test_legacy_user_env_migrates_without_being_deleted(tmp_path: Path) -> None:
    config_dir = tmp_path / "autocedar"
    config_dir.mkdir()
    legacy = config_dir / ".env"
    legacy_contents = (
        "AUTOCEDAR_PROVIDER=local\n"
        "AUTOCEDAR_LOCAL_MODEL=Qwen/Qwen3-32B\n"
        "AUTOCEDAR_LOCAL_BASE_URL=http://jarvis:8000/v1\n"
        "AUTOCEDAR_LOCAL_API_KEY=local-secret\n"
        "ANTHROPIC_API_KEY=anthropic-secret\n"
    )
    legacy.write_text(legacy_contents)

    settings = SettingsStore(config_dir / "settings.json").load()
    auth = AuthStore(config_dir / "auth.json").load()

    assert settings.default_provider == "local"
    assert settings.options_for("local").model == "Qwen/Qwen3-32B"
    assert settings.options_for("local").base_url == "http://jarvis:8000/v1"
    assert settings.legacy_env_migrated is True
    assert auth.get_api_key("local") == "local-secret"
    assert auth.get_api_key("anthropic") == "anthropic-secret"
    assert auth.legacy_env_migrated is True
    assert legacy.exists()
    assert legacy.read_text() == legacy_contents
    assert "local-secret" not in (config_dir / "settings.json").read_text()
    assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(legacy.stat().st_mode) == 0o600
    assert stat.S_IMODE((config_dir / "settings.json").stat().st_mode) == 0o600
    assert stat.S_IMODE((config_dir / "auth.json").stat().st_mode) == 0o600


def test_removed_migrated_key_is_not_reimported(tmp_path: Path) -> None:
    config_dir = tmp_path / "autocedar"
    config_dir.mkdir()
    (config_dir / ".env").write_text("OPENAI_API_KEY=legacy-secret\n")
    store = AuthStore(config_dir / "auth.json")

    assert store.load().get_api_key("openai") == "legacy-secret"
    store.remove_api_key("openai")

    assert store.load().get_api_key("openai") is None
    assert (config_dir / ".env").exists()


def test_legacy_generic_model_migrates_for_selected_provider(tmp_path: Path) -> None:
    config_dir = tmp_path / "autocedar"
    config_dir.mkdir()
    (config_dir / ".env").write_text(
        "AUTOCEDAR_PROVIDER=anthropic\nAUTOCEDAR_MODEL=legacy-claude\n",
    )

    settings = SettingsStore(config_dir / "settings.json").load()

    assert settings.default_provider == "anthropic"
    assert settings.options_for("anthropic").model == "legacy-claude"


def test_legacy_openai_compatible_names_migrate_only_to_selected_local(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "autocedar"
    config_dir.mkdir()
    (config_dir / ".env").write_text(
        "AUTOCEDAR_PROVIDER=vllm\n"
        "AUTOCEDAR_OPENAI_MODEL=legacy-local-model\n"
        "AUTOCEDAR_OPENAI_BASE_URL=http://legacy-local:8000/v1\n",
    )

    settings = SettingsStore(config_dir / "settings.json").load()

    assert settings.default_provider == "local"
    assert settings.options_for("local").model == "legacy-local-model"
    assert settings.options_for("local").base_url == "http://legacy-local:8000/v1"
    assert settings.options_for("openai") == ProviderOptions()


def test_credential_resolution_and_repr_never_expose_secret() -> None:
    auth = ProviderAuth(providers={
        "openai": ProviderCredential("stored-super-secret"),
    })

    resolved = resolve_api_key(
        "openai",
        auth=auth,
        environ={"OPENAI_API_KEY": "environment-super-secret"},
    )

    assert resolved.api_key == "environment-super-secret"
    assert resolved.source == "environment:OPENAI_API_KEY"
    assert "environment-super-secret" not in repr(resolved)
    assert "stored-super-secret" not in repr(auth)
    assert "stored-super-secret" not in repr(auth.providers["openai"])


def test_auth_file_round_trip_is_provider_scoped_and_private(tmp_path: Path) -> None:
    path = tmp_path / "config" / "auth.json"
    store = AuthStore(path)

    store.set_api_key("anthropic", "sk-ant-real")
    store.set_api_key("openai", "sk-openai-real")

    payload = json.loads(path.read_text())
    assert payload["providers"]["anthropic"]["api_key"] == "sk-ant-real"
    assert payload["providers"]["openai"]["api_key"] == "sk-openai-real"
    assert store.get_api_key("anthropic") == "sk-ant-real"
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_malformed_settings_json_has_actionable_error(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"providers":')

    with pytest.raises(ProviderConfigurationError, match="Invalid JSON.*line 1"):
        SettingsStore(path).load(migrate_legacy=False)
