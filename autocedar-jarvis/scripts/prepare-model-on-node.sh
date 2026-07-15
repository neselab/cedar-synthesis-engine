#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

load_config "${1:-}"
require_slurm_job
require_value AUTOCEDAR_VLLM_ENV
require_value AUTOCEDAR_MODEL_REPO
AUTOCEDAR_MODEL_REVISION="${AUTOCEDAR_MODEL_REVISION:-none}"
require_value AUTOCEDAR_MODEL_REVISION
configure_huggingface_paths

VLLM_PYTHON="$AUTOCEDAR_VLLM_ENV/bin/python"
HF_BIN="$AUTOCEDAR_VLLM_ENV/bin/hf"
[[ -x "$VLLM_PYTHON" && -x "$HF_BIN" ]] || fail \
  "The vLLM environment is incomplete at $AUTOCEDAR_VLLM_ENV. Run scripts/install-vllm.sh first."

if [[ "$AUTOCEDAR_MODEL_REPO" == /* ]]; then
  [[ "$AUTOCEDAR_MODEL_REVISION" == "none" ]] || fail \
    "Set AUTOCEDAR_MODEL_REVISION=none when AUTOCEDAR_MODEL_REPO is a local path."
  [[ -d "$AUTOCEDAR_MODEL_REPO" ]] || fail \
    "The configured local model directory does not exist: $AUTOCEDAR_MODEL_REPO"
  MODEL_PATH="$AUTOCEDAR_MODEL_REPO"
  printf 'Using the shared/local model directory: %s\n' "$MODEL_PATH"
else
  HF_DOWNLOAD_ARGS=(
    download "$AUTOCEDAR_MODEL_REPO"
    --cache-dir "$HF_HUB_CACHE"
    --quiet
  )
  if [[ "$AUTOCEDAR_MODEL_REVISION" != "none" ]]; then
    HF_DOWNLOAD_ARGS+=(--revision "$AUTOCEDAR_MODEL_REVISION")
  fi

  printf 'Model-cache space before download:\n'
  df -h "$AUTOCEDAR_MODEL_CACHE"
  printf 'Downloading %s. This can take a while on the first run...\n' "$AUTOCEDAR_MODEL_REPO"
  DOWNLOAD_OUTPUT="$("$HF_BIN" "${HF_DOWNLOAD_ARGS[@]}")"
  MODEL_PATH="$(printf '%s\n' "$DOWNLOAD_OUTPUT" | tail -n 1)"
  [[ -d "$MODEL_PATH" ]] || fail "Hugging Face did not return a usable snapshot path."
fi

printf 'Checking that the downloaded model has a usable chat template...\n'
"$VLLM_PYTHON" - "$MODEL_PATH" <<'PY'
from pathlib import Path
import sys

from transformers import AutoTokenizer

model_path = Path(sys.argv[1])
tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
rendered = tokenizer.apply_chat_template(
    [{"role": "user", "content": "AutoCedar model setup check"}],
    tokenize=False,
    add_generation_prompt=True,
)
if not isinstance(rendered, str) or not rendered.strip():
    raise SystemExit("The model chat template rendered an empty prompt.")
print(f"Chat template: OK ({tokenizer.__class__.__name__})")
print(f"Resolved model snapshot: {model_path}")
if model_path.parent.name == "snapshots":
    print(f"Resolved Hugging Face revision: {model_path.name}")
PY

printf 'Model-cache space after preparation:\n'
df -h "$AUTOCEDAR_MODEL_CACHE"
printf 'Model preparation finished. Run scripts/submit-smoke-test.sh next.\n'
