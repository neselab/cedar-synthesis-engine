"""Tests for AutoCedar environment loading."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from autocedar.env import (
    ANTHROPIC_API_KEY,
    is_real_anthropic_api_key,
    load_dotenv,
    remove_dotenv_value,
    user_config_env_path,
    write_dotenv_value,
    write_user_config_value,
)


def test_load_dotenv_finds_parent_env_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    (tmp_path / ".env").write_text(
        'ANTHROPIC_API_KEY="test-key"\nAUTOCEDAR_CHAT_MODEL=claude-test\n',
    )
    child = tmp_path / "nested"
    child.mkdir()
    monkeypatch.chdir(child)

    loaded = load_dotenv()

    assert loaded == tmp_path / ".env"
    assert os.environ["ANTHROPIC_API_KEY"] == "test-key"
    assert os.environ["AUTOCEDAR_CHAT_MODEL"] == "claude-test"


def test_load_dotenv_does_not_override_existing_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "already-set")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=from-file\n")
    monkeypatch.chdir(tmp_path)

    load_dotenv()

    assert os.environ["ANTHROPIC_API_KEY"] == "already-set"


def test_load_dotenv_uses_user_config_when_project_env_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    user_env = user_config_env_path()
    user_env.parent.mkdir(parents=True)
    user_env.write_text("ANTHROPIC_API_KEY=from-user\n")
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)

    loaded = load_dotenv()

    assert loaded == user_env
    assert os.environ["ANTHROPIC_API_KEY"] == "from-user"


def test_load_dotenv_repairs_existing_user_config_permissions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv(ANTHROPIC_API_KEY, raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    user_env = user_config_env_path()
    user_env.parent.mkdir(parents=True)
    user_env.write_text("ANTHROPIC_API_KEY=from-user\n")
    user_env.parent.chmod(0o755)
    user_env.chmod(0o644)

    load_dotenv(start=tmp_path / "project")

    assert stat.S_IMODE(user_env.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(user_env.stat().st_mode) == 0o600


def test_project_env_overrides_user_config_without_overriding_shell(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    user_env = user_config_env_path()
    user_env.parent.mkdir(parents=True)
    user_env.write_text(
        "ANTHROPIC_API_KEY=from-user\nAUTOCEDAR_CHAT_MODEL=claude-user\n",
    )
    (tmp_path / ".env").write_text(
        "ANTHROPIC_API_KEY=from-project\nAUTOCEDAR_CHAT_MODEL=claude-project\n",
    )
    monkeypatch.chdir(tmp_path)

    load_dotenv()

    assert os.environ["ANTHROPIC_API_KEY"] == "from-project"
    assert os.environ["AUTOCEDAR_CHAT_MODEL"] == "claude-project"


def test_shell_api_key_still_overrides_user_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-shell")
    monkeypatch.setenv("AUTOCEDAR_CHAT_MODEL", "claude-shell")
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    user_env = user_config_env_path()
    user_env.parent.mkdir(parents=True)
    user_env.write_text(
        "ANTHROPIC_API_KEY=from-user\nAUTOCEDAR_CHAT_MODEL=claude-user\n",
    )
    (tmp_path / ".env").write_text(
        "ANTHROPIC_API_KEY=from-project\nAUTOCEDAR_CHAT_MODEL=claude-project\n",
    )
    monkeypatch.chdir(tmp_path)

    load_dotenv()

    assert os.environ["ANTHROPIC_API_KEY"] == "from-shell"
    assert os.environ["AUTOCEDAR_CHAT_MODEL"] == "claude-shell"


def test_write_user_config_value_uses_autocedar_config_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv(ANTHROPIC_API_KEY, raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))

    written = write_user_config_value(ANTHROPIC_API_KEY, "sk-ant-user")

    assert written == tmp_path / "config" / ".env"
    assert written.read_text() == "ANTHROPIC_API_KEY=sk-ant-user\n"
    assert os.environ[ANTHROPIC_API_KEY] == "sk-ant-user"
    assert stat.S_IMODE(written.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(written.stat().st_mode) == 0o600


def test_write_user_config_value_repairs_permissive_modes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    config_dir = tmp_path / "config"
    config_dir.mkdir(mode=0o755)
    env_path = config_dir / ".env"
    env_path.write_text("ANTHROPIC_API_KEY=old\n")
    env_path.chmod(0o644)

    write_user_config_value(ANTHROPIC_API_KEY, "new")

    assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(env_path.stat().st_mode) == 0o600
    assert env_path.read_text() == "ANTHROPIC_API_KEY=new\n"


def test_write_dotenv_value_creates_file_and_sets_process_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv(ANTHROPIC_API_KEY, raising=False)

    env_path = write_dotenv_value(
        ANTHROPIC_API_KEY,
        "sk-ant-test123",
        start=tmp_path,
    )

    assert env_path == tmp_path / ".env"
    assert env_path.read_text() == "ANTHROPIC_API_KEY=sk-ant-test123\n"
    assert os.environ[ANTHROPIC_API_KEY] == "sk-ant-test123"


def test_write_dotenv_value_replaces_placeholder(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(ANTHROPIC_API_KEY, raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("# local config\nANTHROPIC_API_KEY=sk-ant-...\nCVC5=/usr/bin/cvc5\n")

    written = write_dotenv_value(
        ANTHROPIC_API_KEY,
        "sk-ant-realvalue",
        start=tmp_path,
    )

    assert written == env_path
    assert env_path.read_text() == (
        "# local config\nANTHROPIC_API_KEY=sk-ant-realvalue\nCVC5=/usr/bin/cvc5\n"
    )
    assert os.environ[ANTHROPIC_API_KEY] == "sk-ant-realvalue"


def test_remove_dotenv_value_removes_key_and_process_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(ANTHROPIC_API_KEY, "sk-ant-test123")
    env_path = tmp_path / ".env"
    env_path.write_text("ANTHROPIC_API_KEY=sk-ant-test123\nAUTOCEDAR_EFFORT=high\n")

    removed = remove_dotenv_value(ANTHROPIC_API_KEY, start=tmp_path)

    assert removed == env_path
    assert env_path.read_text() == "AUTOCEDAR_EFFORT=high\n"
    assert ANTHROPIC_API_KEY not in os.environ


def test_placeholder_api_key_is_not_real() -> None:
    assert is_real_anthropic_api_key("sk-ant-...") is False
    assert is_real_anthropic_api_key("") is False
    assert is_real_anthropic_api_key("sk-ant-realvalue") is True
