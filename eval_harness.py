"""Backward-compatible wrapper for ``autocedar.harness.eval_harness``."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("AUTOCEDAR_ROOT", os.path.dirname(os.path.abspath(__file__)))

from autocedar.harness.eval_harness import *  # noqa: F401,F403,E402
from autocedar.harness.eval_harness import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
