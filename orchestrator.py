"""Backward-compatible wrapper for ``autocedar.harness.orchestrator``."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("AUTOCEDAR_ROOT", os.path.dirname(os.path.abspath(__file__)))

from autocedar.harness.orchestrator import *  # noqa: F401,F403,E402
from autocedar.harness.orchestrator import main  # noqa: E402


if __name__ == "__main__":
    loss = main()
    sys.exit(0 if loss == 0 else 1)
