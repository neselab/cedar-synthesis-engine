#!/usr/bin/env bash
set -euo pipefail

SLURM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
BUNDLE_ROOT="$(cd "$SLURM_DIR/.." && pwd -P)"

exec bash -l \
  "$BUNDLE_ROOT/scripts/run-on-node.sh" \
  --smoke-test \
  "${1:?Pass the absolute path to config/jarvis.env}"
