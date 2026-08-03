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
  --upgrade \
  --python "$AUTOCEDAR_VLLM_ENV/bin/python" \
  "vllm>=0.19.0" \
  "huggingface-hub>=0.34.0" \
  "jinja2>=3.1.0" \
  "ninja>=1.11.0" \
  --torch-backend=auto

"$AUTOCEDAR_VLLM_ENV/bin/vllm" --version
"$AUTOCEDAR_VLLM_ENV/bin/python" -c \
  'import huggingface_hub; print(f"huggingface-hub {huggingface_hub.__version__}")'
printf 'vLLM installation finished at %s.\n' "$AUTOCEDAR_VLLM_ENV"
