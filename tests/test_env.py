"""Tests for AutoCedar environment loading."""

from __future__ import annotations

import os
from pathlib import Path

from autocedar.env import (
    ANTHROPIC_API_KEY,
    is_real_anthropic_api_key,
    load_dotenv,
    remove_dotenv_value,
    write_dotenv_value,
)


def test_load_dotenv_finds_parent_env_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)
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
