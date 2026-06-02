"""Session save/resume.

See ``docs/HITL_STEP_B_PLAN.md`` §7.1 — resume is mandatory because
the user-attention budget (~30 minutes) is too long to lose to a crash.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_SESSION_FILE = ".session.json"


def save_session_state(output_dir: Path, state: dict[str, Any]) -> None:
    """Atomically write the session state to ``<output_dir>/.session.json``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / _SESSION_FILE
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(target)


def load_session_state(output_dir: Path) -> dict[str, Any] | None:
    """Return the saved session state if present; else ``None``."""
    target = output_dir / _SESSION_FILE
    if not target.exists():
        return None
    return json.loads(target.read_text())
