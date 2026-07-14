#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

load_config "${1:-}"
build_gpu_slurm_args

command -v sbatch >/dev/null 2>&1 || fail "sbatch is not available; run this command on a Jarvis login node."
mkdir -m 700 -p "$BUNDLE_ROOT/logs"
chmod 700 "$BUNDLE_ROOT/logs"

sbatch \
  --job-name=autocedar-smoke \
  "${SLURM_ARGS[@]}" \
  --chdir="$BUNDLE_ROOT" \
  --output="$BUNDLE_ROOT/logs/autocedar-smoke-%j.out" \
  "$BUNDLE_ROOT/slurm/autocedar-smoke.sbatch" \
  "$CONFIG_FILE"
