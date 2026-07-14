"""Environment loading helpers for AutoCedar."""

from __future__ import annotations

import os
import shlex
import tempfile
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
    "[redacted]",
    "[redacted-api-key]",
    "redacted-api-key",
}


def load_dotenv(start: Path | None = None) -> Path | None:
    """Load user config and project config without overriding the shell.

    Precedence is shell environment, then the nearest project ``.env``, then
    the user-level AutoCedar config. This lets a project intentionally select
    its own credentials and models while preserving explicit shell overrides.
    """
    preexisting_keys = set(os.environ)
    env_path = find_dotenv(start or Path.cwd())
    loaded: Path | None = None
    user_env = user_config_env_path()
    # AutoCedar 0.2 stores provider settings and credentials in split JSON
    # files. Once either store exists, keep loading unrelated operational
    # settings (CEDAR, CVC5, etc.) from the legacy file but filter every key
    # owned by the split stores. Otherwise a removed credential or provider
    # choice could be reintroduced into os.environ and outrank the JSON stores.
    if user_env.exists():
        _secure_existing_user_config(user_env)
        if _split_provider_config_exists():
            loaded_keys = _load_env_file(
                user_env,
                excluded_keys=_migrated_provider_env_keys(),
            )
            if loaded_keys:
                loaded = user_env
        else:
            _load_env_file(user_env)
            loaded = user_env

    if env_path is not None:
        project_overrides = _env_file_keys(env_path) - preexisting_keys
        _load_env_file(env_path, override_keys=project_overrides)
        loaded = env_path
    return loaded


def _split_provider_config_exists() -> bool:
    from autocedar.providers.auth import auth_path
    from autocedar.providers.config import settings_path

    return settings_path().exists() or auth_path().exists()


def _migrated_provider_env_keys() -> frozenset[str]:
    """Keys whose legacy values are superseded by settings/auth JSON stores."""

    from autocedar.providers.auth import MIGRATED_AUTH_ENV_KEYS
    from autocedar.providers.config import MIGRATED_SETTINGS_ENV_KEYS

    return MIGRATED_SETTINGS_ENV_KEYS | MIGRATED_AUTH_ENV_KEYS


def _load_env_file(
    env_path: Path,
    *,
    override_keys: set[str] | None = None,
    excluded_keys: frozenset[str] | set[str] | None = None,
) -> set[str]:
    overrides = override_keys or set()
    excluded = excluded_keys or set()
    loaded: set[str] = set()
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
        if (
            not key
            or key in excluded
            or (key in os.environ and key not in overrides)
        ):
            continue
        os.environ[key] = _parse_env_value(value)
        loaded.add(key)
    return loaded


def write_dotenv_value(
    key: str,
    value: str,
    *,
    start: Path | None = None,
    env_path: Path | None = None,
) -> Path:
    """Create or update ``key=value`` in the nearest ``.env`` file."""
    target = _resolve_dotenv_for_write(start=start, env_path=env_path)
    _prepare_env_parent(target)

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
    _write_private_env_file(target, "\n".join(updated) + "\n")
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
    _prepare_env_parent(target)
    lines = target.read_text().splitlines() if target.exists() else []
    remaining = [line for line in lines if _line_key(line) != key]
    _write_private_env_file(
        target,
        ("\n".join(remaining) + "\n") if remaining else "",
    )
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


def _env_file_keys(env_path: Path) -> set[str]:
    """Return the variable names declared by an env file."""
    return {
        key
        for raw_line in env_path.read_text().splitlines()
        if (key := _line_key(raw_line)) is not None
    }


def _prepare_env_parent(target: Path) -> None:
    """Create the target parent and secure the user config directory."""
    user_target = user_config_env_path().expanduser().resolve()
    is_user_config = target == user_target
    target.parent.mkdir(
        mode=0o700 if is_user_config else 0o777,
        parents=True,
        exist_ok=True,
    )
    if is_user_config:
        os.chmod(target.parent, 0o700)


def _secure_existing_user_config(target: Path) -> None:
    """Repair permissions left by older AutoCedar releases before reading."""
    os.chmod(target.parent, 0o700)
    os.chmod(target, 0o600)


def _write_private_env_file(target: Path, contents: str) -> None:
    """Atomically replace an env file with mode 0600 from its creation."""
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        dir=target.parent,
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
        os.replace(temporary, target)
    finally:
        if fd >= 0:
            os.close(fd)
        temporary.unlink(missing_ok=True)


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
