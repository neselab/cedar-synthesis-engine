#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

MODE="interactive"
if [[ "${1:-}" == "--doctor-only" ]]; then
  MODE="doctor-only"
  shift
fi
load_config "${1:-}"
require_slurm_job

for name in \
  AUTOCEDAR_VLLM_ENV \
  AUTOCEDAR_MODEL_REPO \
  AUTOCEDAR_MODEL_NAME \
  AUTOCEDAR_MODEL_CACHE \
  AUTOCEDAR_MODEL_PORT \
  AUTOCEDAR_MAX_MODEL_LEN \
  AUTOCEDAR_GPU_MEMORY_UTILIZATION \
  AUTOCEDAR_STARTUP_TIMEOUT_SECONDS \
  AUTOCEDAR_LOCAL_MAX_TOKENS \
  AUTOCEDAR_LOCAL_TIMEOUT_SECONDS \
  AUTOCEDAR_LOCAL_STRUCTURED_OUTPUT; do
  require_value "$name"
done
require_positive_integer JARVIS_GPU_COUNT
require_positive_integer AUTOCEDAR_MODEL_PORT
require_positive_integer AUTOCEDAR_MAX_MODEL_LEN
require_positive_integer AUTOCEDAR_STARTUP_TIMEOUT_SECONDS
require_positive_integer AUTOCEDAR_LOCAL_MAX_TOKENS
require_positive_integer AUTOCEDAR_LOCAL_TIMEOUT_SECONDS
[[ "$AUTOCEDAR_MODEL_CACHE" == /* ]] || fail "AUTOCEDAR_MODEL_CACHE must be an absolute path."

load_gpu_module
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export CEDAR="${CEDAR:-$HOME/.cargo/bin/cedar}"
export CVC5="${CVC5:-$HOME/.local/bin/cvc5}"
export HF_HOME="$AUTOCEDAR_MODEL_CACHE"

command -v autocedar >/dev/null 2>&1 || fail "autocedar is not installed. Complete README step 4 first."
command -v curl >/dev/null 2>&1 || fail "curl is required on the GPU node."
command -v nvidia-smi >/dev/null 2>&1 || fail "nvidia-smi is unavailable in this GPU job."
VLLM_BIN="$AUTOCEDAR_VLLM_ENV/bin/vllm"
VLLM_PYTHON="$AUTOCEDAR_VLLM_ENV/bin/python"
[[ -x "$VLLM_BIN" && -x "$VLLM_PYTHON" ]] || fail \
  "vLLM is not installed at $AUTOCEDAR_VLLM_ENV. Run scripts/install-vllm.sh first."

mkdir -p "$AUTOCEDAR_MODEL_CACHE"
mkdir -m 700 -p "$BUNDLE_ROOT/logs"
VLLM_LOG="$BUNDLE_ROOT/logs/vllm-${SLURM_JOB_ID}.log"
: >"$VLLM_LOG"
chmod 600 "$VLLM_LOG"
LOCAL_API_KEY="$($VLLM_PYTHON -c 'import secrets; print(secrets.token_urlsafe(32))')"
LOCAL_BASE_URL="http://127.0.0.1:${AUTOCEDAR_MODEL_PORT}/v1"
# vLLM supports VLLM_API_KEY directly. Keep the per-job secret out of the
# process argument list, which can be visible to other users on a shared node.
export VLLM_API_KEY="$LOCAL_API_KEY"

VLLM_COMMAND=(
  "$VLLM_BIN" serve "$AUTOCEDAR_MODEL_REPO"
  --host 127.0.0.1
  --port "$AUTOCEDAR_MODEL_PORT"
  --served-model-name "$AUTOCEDAR_MODEL_NAME"
  --max-model-len "$AUTOCEDAR_MAX_MODEL_LEN"
  --gpu-memory-utilization "$AUTOCEDAR_GPU_MEMORY_UTILIZATION"
)
if (( JARVIS_GPU_COUNT > 1 )); then
  VLLM_COMMAND+=(--tensor-parallel-size "$JARVIS_GPU_COUNT")
fi

VLLM_PID=""
cleanup() {
  local status=$?
  trap - EXIT
  if [[ -n "$VLLM_PID" ]] && kill -0 "$VLLM_PID" 2>/dev/null; then
    printf '\nStopping local model server...\n'
    kill "$VLLM_PID" 2>/dev/null || true
    for _ in {1..20}; do
      if ! kill -0 "$VLLM_PID" 2>/dev/null; then
        break
      fi
      sleep 1
    done
    if kill -0 "$VLLM_PID" 2>/dev/null; then
      printf 'Model server did not stop after 20 seconds; forcing shutdown.\n' >&2
      kill -9 "$VLLM_PID" 2>/dev/null || true
    fi
    wait "$VLLM_PID" 2>/dev/null || true
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

printf 'GPU node: %s\n' "$(hostname)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
printf 'Starting local model %s...\n' "$AUTOCEDAR_MODEL_REPO"
printf 'vLLM log: %s\n' "$VLLM_LOG"
"${VLLM_COMMAND[@]}" >"$VLLM_LOG" 2>&1 &
VLLM_PID=$!
unset VLLM_API_KEY

deadline=$((SECONDS + AUTOCEDAR_STARTUP_TIMEOUT_SECONDS))
ready="false"
while (( SECONDS < deadline )); do
  if curl -fsS \
    -H "Authorization: Bearer $LOCAL_API_KEY" \
    "$LOCAL_BASE_URL/models" >/dev/null; then
    ready="true"
    break
  fi
  if ! kill -0 "$VLLM_PID" 2>/dev/null; then
    printf 'vLLM exited before becoming ready. Last log lines:\n' >&2
    tail -n 80 "$VLLM_LOG" >&2 || true
    fail "Local model server failed to start."
  fi
  printf 'Model is still loading; checking again in 5 seconds...\n'
  sleep 5
done
if [[ "$ready" != "true" ]]; then
  tail -n 80 "$VLLM_LOG" >&2 || true
  fail "Model server did not become ready within $AUTOCEDAR_STARTUP_TIMEOUT_SECONDS seconds."
fi

export AUTOCEDAR_PROVIDER="local"
export AUTOCEDAR_LOCAL_BASE_URL="$LOCAL_BASE_URL"
export AUTOCEDAR_LOCAL_API_KEY="$LOCAL_API_KEY"
export AUTOCEDAR_LOCAL_MODEL="$AUTOCEDAR_MODEL_NAME"
export AUTOCEDAR_LOCAL_MAX_TOKENS
export AUTOCEDAR_LOCAL_TIMEOUT_SECONDS
export AUTOCEDAR_LOCAL_STRUCTURED_OUTPUT
export AUTOCEDAR_MODEL="$AUTOCEDAR_MODEL_NAME"
export AUTOCEDAR_AUTHOR_MODEL="$AUTOCEDAR_MODEL_NAME"
export AUTOCEDAR_CHAT_MODEL="$AUTOCEDAR_MODEL_NAME"

printf 'Local model server is ready. Running AutoCedar doctor...\n'
autocedar doctor

if [[ "$MODE" == "doctor-only" ]]; then
  printf 'Smoke test passed. This validates plumbing only, not policy meaning.\n'
  exit 0
fi

printf '\nOpening AutoCedar. Use /settings and /models to inspect the connection.\n'
printf 'Quit AutoCedar normally to stop vLLM and release this job.\n\n'
autocedar
