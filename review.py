"""Backward-compatible wrapper for ``autocedar.harness.review``."""

from __future__ import annotations

import os

os.environ.setdefault(
    "AUTOCEDAR_WORKSPACE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace"),
)

from autocedar.harness.review import *  # noqa: F401,F403,E402
from autocedar.harness.review import main  # noqa: E402


if __name__ == "__main__":
    main()
