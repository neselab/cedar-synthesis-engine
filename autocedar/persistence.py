"""Crash-safe local writes shared by authoring and the terminal UI."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2))


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def session_spec(session: Path) -> Path:
    inputs = sorted((session / "input").glob("*"))
    inputs = [path for path in inputs if path.is_file() and not path.name.startswith(".")]
    if len(inputs) != 1:
        raise ValueError(f"Expected one archived input spec in {session / 'input'}")
    return inputs[0]


def find_resumable_session(output_dir: Path, spec_text: str) -> Path | None:
    """Find an unfinished session for exactly this input, newest first."""
    if not output_dir.exists():
        return None
    candidates = sorted(
        (p for p in output_dir.iterdir() if p.is_dir()),
        key=lambda p: p.stat().st_mtime_ns,
        reverse=True,
    )
    for path in candidates:
        if (path / "stage2_5" / "final_user_decision.json").exists():
            continue
        if not ((path / "stage1" / "final_schema.cedarschema").exists()
                or (path / "stage1" / "checkpoint.json").exists()):
            continue
        try:
            if session_spec(path).read_text() == spec_text:
                return path
        except (OSError, ValueError):
            continue
    return None
