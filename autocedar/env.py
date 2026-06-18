"""Environment loading helpers for AutoCedar."""

from __future__ import annotations

import os
import shlex
from pathlib import Path

ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
USER_CONFIG_DIR_ENV = "AUTOCEDAR_CONFIG_DIR"
_PLACEHOLDER_API_KEYS = {
    "",
    "sk-ant-...",
    "sk-ant-…",
    "your-api-key",
    "your-anthropic-api-key",
    "<your-anthropic-api-key>",
}


def load_dotenv(start: Path | None = None) -> Path | None:
    """Load project ``.env`` first, then user config for missing values."""
    env_path = find_dotenv(start or Path.cwd())
    loaded: Path | None = None
    if env_path is not None:
        _load_env_file(env_path)
        loaded = env_path

    user_env = user_config_env_path()
    if user_env.exists():
        _load_env_file(user_env)
        loaded = loaded or user_env
    return loaded


def _load_env_file(env_path: Path) -> None:
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


def write_dotenv_value(
    key: str,
    value: str,
    *,
    start: Path | None = None,
    env_path: Path | None = None,
) -> Path:
    """Create or update ``key=value`` in the nearest ``.env`` file."""
    target = _resolve_dotenv_for_write(start=start, env_path=env_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    lines = target.read_text().splitlines() if target.exists() else []
    formatted = f"{key}={_format_env_value(value)}"
    replaced = False
    updated: list[str] = []
    for line in lines:
        parsed = _line_key(line)
        if parsed == key:
            prefix = "export " if line.lstrip().startswith("export ") else ""
            updated.append(f"{prefix}{formatted}")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        if updated and updated[-1].strip():
            updated.append("")
        updated.append(formatted)
    target.write_text("\n".join(updated) + "\n", encoding="utf-8")
    os.environ[key] = value
    return target


def write_user_config_value(key: str, value: str) -> Path:
    """Create or update ``key=value`` in the user-level AutoCedar config."""
    return write_dotenv_value(key, value, env_path=user_config_env_path())


def remove_user_config_value(key: str) -> Path:
    """Remove ``key`` from the user-level AutoCedar config."""
    return remove_dotenv_value(key, env_path=user_config_env_path())


def remove_dotenv_value(
    key: str,
    *,
    start: Path | None = None,
    env_path: Path | None = None,
) -> Path:
    """Remove ``key`` from the nearest ``.env`` file, creating it if needed."""
    target = _resolve_dotenv_for_write(start=start, env_path=env_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = target.read_text().splitlines() if target.exists() else []
    remaining = [line for line in lines if _line_key(line) != key]
    target.write_text(("\n".join(remaining) + "\n") if remaining else "", encoding="utf-8")
    os.environ.pop(key, None)
    return target


def is_real_anthropic_api_key(value: str | None) -> bool:
    """Return true when ``value`` looks like a user-supplied Anthropic key."""
    if value is None:
        return False
    stripped = value.strip().strip("\"'")
    if stripped.lower() in _PLACEHOLDER_API_KEYS:
        return False
    return bool(stripped)


def find_dotenv(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        candidate = directory / ".env"
        if candidate.exists():
            return candidate
    return None


def user_config_env_path() -> Path:
    root = os.environ.get(USER_CONFIG_DIR_ENV)
    if root:
        return Path(root).expanduser() / ".env"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "autocedar" / ".env"
    return Path.home() / ".config" / "autocedar" / ".env"


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


def _resolve_dotenv_for_write(
    *,
    start: Path | None,
    env_path: Path | None,
) -> Path:
    if env_path is not None:
        return env_path.expanduser().resolve()
    base = (start or Path.cwd()).resolve()
    existing = find_dotenv(base)
    if existing is not None:
        return existing
    if base.is_file():
        base = base.parent
    return base / ".env"


def _line_key(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export "):].strip()
    if "=" not in stripped:
        return None
    key, _ = stripped.split("=", 1)
    key = key.strip()
    return key or None


def _format_env_value(value: str) -> str:
    stripped = value.strip()
    if stripped and all(ch.isalnum() or ch in "_-./:@" for ch in stripped):
        return stripped
    return shlex.quote(stripped)
