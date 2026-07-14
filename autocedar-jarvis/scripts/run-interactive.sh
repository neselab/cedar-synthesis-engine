#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

load_config "${1:-}"
build_gpu_slurm_args

command -v srun >/dev/null 2>&1 || fail "srun is not available; run this command on a Jarvis login node."
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  fail "A Slurm job is already active. Exit it, then run this launcher from the login node."
fi

printf 'Requesting a GPU for AutoCedar...\n'
srun \
  --job-name=autocedar-local \
  "${SLURM_ARGS[@]}" \
  --pty \
  bash -l "$SCRIPT_DIR/run-on-node.sh" "$CONFIG_FILE"
