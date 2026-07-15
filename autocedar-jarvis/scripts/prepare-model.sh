#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

load_config "${1:-}"
build_cpu_slurm_args

command -v srun >/dev/null 2>&1 || fail "srun is not available; run this command on a Jarvis login node."

printf 'Requesting a CPU job to download and check the model...\n'
srun \
  --job-name=autocedar-model-prepare \
  "${SLURM_ARGS[@]}" \
  bash -l "$SCRIPT_DIR/prepare-model-on-node.sh" "$CONFIG_FILE"
