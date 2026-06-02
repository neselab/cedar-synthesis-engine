"""Tests for AutoCedar environment loading."""

from __future__ import annotations

import os
from pathlib import Path

from autocedar.env import load_dotenv


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
