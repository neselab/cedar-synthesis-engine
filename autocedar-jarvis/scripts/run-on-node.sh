#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

MODE="interactive"
if [[ "${1:-}" == "--smoke-test" ]]; then
  MODE="smoke-test"
  shift
fi
load_config "${1:-}"
require_slurm_job

# Keep older local config files usable after the model-specific switches were
# added to the template.
AUTOCEDAR_MODEL_REVISION="${AUTOCEDAR_MODEL_REVISION:-none}"
AUTOCEDAR_MAX_NUM_SEQS="${AUTOCEDAR_MAX_NUM_SEQS:-128}"
AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY="${AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY:-false}"
AUTOCEDAR_VLLM_REASONING_PARSER="${AUTOCEDAR_VLLM_REASONING_PARSER:-none}"
AUTOCEDAR_VLLM_ENABLE_THINKING="${AUTOCEDAR_VLLM_ENABLE_THINKING:-default}"

for name in \
  AUTOCEDAR_VLLM_ENV \
  AUTOCEDAR_MODEL_REPO \
  AUTOCEDAR_MODEL_NAME \
  AUTOCEDAR_MODEL_REVISION \
  AUTOCEDAR_MODEL_CACHE \
  AUTOCEDAR_MODEL_PORT \
  AUTOCEDAR_MAX_MODEL_LEN \
  AUTOCEDAR_MAX_NUM_SEQS \
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
require_positive_integer AUTOCEDAR_MAX_NUM_SEQS
require_positive_integer AUTOCEDAR_STARTUP_TIMEOUT_SECONDS
require_positive_integer AUTOCEDAR_LOCAL_MAX_TOKENS
require_positive_integer AUTOCEDAR_LOCAL_TIMEOUT_SECONDS
case "$AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY" in
  true|false) ;;
  *) fail "AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY must be true or false." ;;
esac
case "$AUTOCEDAR_VLLM_ENABLE_THINKING" in
  default|true|false) ;;
  *) fail "AUTOCEDAR_VLLM_ENABLE_THINKING must be default, true, or false." ;;
esac
if [[ "$AUTOCEDAR_VLLM_REASONING_PARSER" != "none" ]] && \
  [[ ! "$AUTOCEDAR_VLLM_REASONING_PARSER" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]]; then
  fail "AUTOCEDAR_VLLM_REASONING_PARSER contains unsupported characters."
fi
if [[ "$AUTOCEDAR_MODEL_REPO" == /* && "$AUTOCEDAR_MODEL_REVISION" != "none" ]]; then
  fail "Set AUTOCEDAR_MODEL_REVISION=none when AUTOCEDAR_MODEL_REPO is a local path."
fi

load_gpu_module
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export CEDAR="${CEDAR:-$HOME/.cargo/bin/cedar}"
export CVC5="${CVC5:-$HOME/.local/bin/cvc5}"
# Jarvis currently exposes CUDA 12.2 with GCC 13. FlashInfer's sampler tries
# to JIT-compile CUDA code with that unsupported pairing and fails in glibc's
# _Float32 declarations. vLLM supports disabling only this sampler and then
# uses its PyTorch-native top-k/top-p implementation instead.
export VLLM_USE_FLASHINFER_SAMPLER="0"
configure_huggingface_paths

command -v autocedar >/dev/null 2>&1 || fail "autocedar is not installed. Complete README step 4 first."
command -v nvidia-smi >/dev/null 2>&1 || fail "nvidia-smi is unavailable in this GPU job."
VLLM_BIN="$AUTOCEDAR_VLLM_ENV/bin/vllm"
VLLM_PYTHON="$AUTOCEDAR_VLLM_ENV/bin/python"
[[ -x "$VLLM_BIN" && -x "$VLLM_PYTHON" ]] || fail \
  "vLLM is not installed at $AUTOCEDAR_VLLM_ENV. Run scripts/install-vllm.sh first."

mkdir -m 700 -p "$BUNDLE_ROOT/logs"
VLLM_LOG="$BUNDLE_ROOT/logs/vllm-${SLURM_JOB_ID}.log"
: >"$VLLM_LOG"
chmod 600 "$VLLM_LOG"
LOCAL_API_KEY="$($VLLM_PYTHON -c 'import secrets; print(secrets.token_urlsafe(32))')"
PREFERRED_MODEL_PORT="$AUTOCEDAR_MODEL_PORT"
AUTOCEDAR_MODEL_PORT="$(
  "$VLLM_PYTHON" "$SCRIPT_DIR/select_port.py" \
    --preferred "$PREFERRED_MODEL_PORT" \
    --job-id "$SLURM_JOB_ID"
)" || fail "Could not choose a free loopback port for this model-server job."
LOCAL_BASE_URL="http://127.0.0.1:${AUTOCEDAR_MODEL_PORT}/v1"
# vLLM supports VLLM_API_KEY directly. Keep the per-job secret out of the
# process argument list, which can be visible to other users on a shared node.
export VLLM_API_KEY="$LOCAL_API_KEY"
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

VLLM_COMMAND=(
  "$VLLM_BIN" serve "$AUTOCEDAR_MODEL_REPO"
  --host 127.0.0.1
  --port "$AUTOCEDAR_MODEL_PORT"
  --served-model-name "$AUTOCEDAR_MODEL_NAME"
  --max-model-len "$AUTOCEDAR_MAX_MODEL_LEN"
  --max-num-seqs "$AUTOCEDAR_MAX_NUM_SEQS"
  --gpu-memory-utilization "$AUTOCEDAR_GPU_MEMORY_UTILIZATION"
)
if (( JARVIS_GPU_COUNT > 1 )); then
  VLLM_COMMAND+=(--tensor-parallel-size "$JARVIS_GPU_COUNT")
fi
if [[ "$AUTOCEDAR_MODEL_REPO" != /* && "$AUTOCEDAR_MODEL_REVISION" != "none" ]]; then
  VLLM_COMMAND+=(--revision "$AUTOCEDAR_MODEL_REVISION")
fi
if [[ "$AUTOCEDAR_VLLM_LANGUAGE_MODEL_ONLY" == "true" ]]; then
  VLLM_COMMAND+=(--language-model-only)
fi
if [[ "$AUTOCEDAR_VLLM_REASONING_PARSER" != "none" ]]; then
  VLLM_COMMAND+=(--reasoning-parser "$AUTOCEDAR_VLLM_REASONING_PARSER")
fi
case "$AUTOCEDAR_VLLM_ENABLE_THINKING" in
  true)
    VLLM_COMMAND+=(--default-chat-template-kwargs '{"enable_thinking": true}')
    ;;
  false)
    VLLM_COMMAND+=(--default-chat-template-kwargs '{"enable_thinking": false}')
    ;;
esac

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
if [[ "$AUTOCEDAR_MODEL_PORT" != "$PREFERRED_MODEL_PORT" ]]; then
  printf 'Port %s is already in use on this shared node; using private job port %s instead.\n' \
    "$PREFERRED_MODEL_PORT" "$AUTOCEDAR_MODEL_PORT"
fi
printf 'Starting local model %s...\n' "$AUTOCEDAR_MODEL_REPO"
printf 'Local endpoint for this job: %s\n' "$LOCAL_BASE_URL"
printf 'vLLM log: %s\n' "$VLLM_LOG"
"${VLLM_COMMAND[@]}" >"$VLLM_LOG" 2>&1 &
VLLM_PID=$!
unset VLLM_API_KEY

deadline=$((SECONDS + AUTOCEDAR_STARTUP_TIMEOUT_SECONDS))
ready="false"
while (( SECONDS < deadline )); do
  if ! kill -0 "$VLLM_PID" 2>/dev/null; then
    printf 'vLLM exited before becoming ready. Last log lines:\n' >&2
    tail -n 80 "$VLLM_LOG" >&2 || true
    fail "Local model server failed to start."
  fi
  # A shared node may already have another user's server. Readiness therefore
  # requires this job's expected served-model name, not merely any HTTP 200.
  if "$VLLM_PYTHON" "$SCRIPT_DIR/model_smoke.py" --readiness-check \
    >/dev/null 2>&1; then
    ready="true"
    break
  fi
  printf 'Model is still loading; checking again in 5 seconds...\n'
  sleep 5
done
if [[ "$ready" != "true" ]]; then
  tail -n 80 "$VLLM_LOG" >&2 || true
  fail "Model server did not become ready within $AUTOCEDAR_STARTUP_TIMEOUT_SECONDS seconds."
fi

printf 'Local model server is ready. Running AutoCedar doctor...\n'
autocedar doctor

if [[ "$MODE" == "smoke-test" ]]; then
  printf 'Testing ordinary and JSON-schema model generation...\n'
  "$VLLM_PYTHON" "$SCRIPT_DIR/model_smoke.py"
  printf 'Smoke test passed. This validates model plumbing only, not policy meaning.\n'
  exit 0
fi

printf '\nOpening AutoCedar. Use /settings and /models to inspect the connection.\n'
printf 'Quit AutoCedar normally to stop vLLM and release this job.\n\n'
autocedar
