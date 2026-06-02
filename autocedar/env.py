"""Environment loading helpers for AutoCedar."""

from __future__ import annotations

import os
import shlex
from pathlib import Path


def load_dotenv(start: Path | None = None) -> Path | None:
    """Load the nearest ``.env`` without overriding existing environment vars."""
    env_path = find_dotenv(start or Path.cwd())
    if env_path is None:
        return None

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _parse_env_value(value)
    return env_path


def find_dotenv(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        candidate = directory / ".env"
        if candidate.exists():
            return candidate
    return None


def _parse_env_value(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    try:
        parts = shlex.split(stripped, comments=True, posix=True)
    except ValueError:
        return stripped.strip("\"'")
    if not parts:
        return ""
    return parts[0]
