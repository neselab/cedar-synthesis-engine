#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

load_config "${1:-}"
require_slurm_job
require_value AUTOCEDAR_VLLM_ENV
load_gpu_module

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
command -v uv >/dev/null 2>&1 || fail "uv is not installed. Complete README step 4 first."
command -v nvidia-smi >/dev/null 2>&1 || fail "nvidia-smi is unavailable in this GPU job."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

if [[ ! -x "$AUTOCEDAR_VLLM_ENV/bin/python" ]]; then
  uv venv "$AUTOCEDAR_VLLM_ENV" --python 3.12
fi
uv pip install \
  --python "$AUTOCEDAR_VLLM_ENV/bin/python" \
  vllm \
  --torch-backend=auto

"$AUTOCEDAR_VLLM_ENV/bin/vllm" --version
printf 'vLLM installation finished at %s.\n' "$AUTOCEDAR_VLLM_ENV"
