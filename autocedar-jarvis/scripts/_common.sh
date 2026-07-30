#!/usr/bin/env bash

# Shared helpers for the Jarvis launch scripts. This file is sourced, not run.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
BUNDLE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

absolute_path() {
  local requested="$1"
  local parent
  parent="$(cd "$(dirname "$requested")" 2>/dev/null && pwd -P)" || return 1
  printf '%s/%s\n' "$parent" "$(basename "$requested")"
}

load_config() {
  local requested="${1:-$BUNDLE_ROOT/config/jarvis.env}"
  [[ -f "$requested" ]] || fail \
    "Config not found: $requested. Copy config/jarvis.env.example to config/jarvis.env first."
  CONFIG_FILE="$(absolute_path "$requested")" || fail "Cannot resolve config path: $requested"
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
}

require_value() {
  local name="$1"
  local value="${!name-}"
  [[ -n "$value" ]] || fail "$name is empty in $CONFIG_FILE"
  [[ "$value" != *REPLACE_WITH_* ]] || fail "$name still contains a REPLACE_WITH_ placeholder"
}

require_positive_integer() {
  local name="$1"
  local value="${!name-}"
  [[ "$value" =~ ^[1-9][0-9]*$ ]] || fail "$name must be a positive integer (found: ${value:-empty})"
}

configure_huggingface_paths() {
  AUTOCEDAR_HF_HOME="${AUTOCEDAR_HF_HOME:-$HOME/.config/autocedar/huggingface}"
  require_value AUTOCEDAR_MODEL_CACHE
  require_value AUTOCEDAR_HF_HOME
  [[ "$AUTOCEDAR_MODEL_CACHE" == /* ]] || fail \
    "AUTOCEDAR_MODEL_CACHE must be an absolute path."
  [[ "$AUTOCEDAR_HF_HOME" == /* ]] || fail \
    "AUTOCEDAR_HF_HOME must be an absolute path after shell expansion."

  # Keep credentials in the user's private home-backed directory even when
  # weights live in a shared or project scratch cache.
  export HF_HOME="$AUTOCEDAR_HF_HOME"
  export HF_TOKEN_PATH="$AUTOCEDAR_HF_HOME/token"
  export HF_HUB_CACHE="$AUTOCEDAR_MODEL_CACHE/hub"
  export HF_XET_CACHE="$AUTOCEDAR_MODEL_CACHE/xet"
  mkdir -p "$HF_HOME" "$HF_HUB_CACHE" "$HF_XET_CACHE"
  chmod 700 "$HF_HOME"
}

add_optional_slurm_identity_args() {
  require_value JARVIS_SLURM_ACCOUNT
  case "$JARVIS_SLURM_ACCOUNT" in
    [Nn][Oo][Nn][Ee]) ;;
    *) SLURM_ARGS+=(--account="$JARVIS_SLURM_ACCOUNT") ;;
  esac
  if [[ -n "${JARVIS_SLURM_QOS:-}" ]]; then
    case "$JARVIS_SLURM_QOS" in
      [Nn][Oo][Nn][Ee]) ;;
      *)
        [[ "$JARVIS_SLURM_QOS" != *REPLACE_WITH_* ]] || fail "JARVIS_SLURM_QOS still contains a placeholder"
        SLURM_ARGS+=(--qos="$JARVIS_SLURM_QOS")
        ;;
    esac
  fi
}

build_gpu_slurm_args() {
  require_value JARVIS_GPU_PARTITION
  require_value JARVIS_GPU_MEMORY
  require_value JARVIS_GPU_TIME
  require_positive_integer JARVIS_GPU_COUNT
  require_positive_integer JARVIS_GPU_CPUS
  SLURM_ARGS=(
    --nodes=1
    --ntasks=1
    --partition="$JARVIS_GPU_PARTITION"
    --cpus-per-task="$JARVIS_GPU_CPUS"
    --mem="$JARVIS_GPU_MEMORY"
    --time="$JARVIS_GPU_TIME"
    --gres="gpu:$JARVIS_GPU_COUNT"
    --export=ALL
  )
  add_optional_slurm_identity_args
}

build_cpu_slurm_args() {
  require_value JARVIS_CPU_PARTITION
  require_value JARVIS_CPU_MEMORY
  require_value JARVIS_CPU_TIME
  require_positive_integer JARVIS_CPU_CPUS
  SLURM_ARGS=(
    --nodes=1
    --ntasks=1
    --partition="$JARVIS_CPU_PARTITION"
    --cpus-per-task="$JARVIS_CPU_CPUS"
    --mem="$JARVIS_CPU_MEMORY"
    --time="$JARVIS_CPU_TIME"
    --export=ALL
  )
  add_optional_slurm_identity_args
}

load_gpu_module() {
  require_value JARVIS_CUDA_MODULE
  case "$JARVIS_CUDA_MODULE" in
    [Nn][Oo][Nn][Ee]) return ;;
  esac
  type module >/dev/null 2>&1 || fail \
    "The environment-modules command is unavailable. Ask which login shell/module setup Jarvis requires."
  module load "$JARVIS_CUDA_MODULE"
}

configure_cuda_122_host_compiler() {
  command -v nvcc >/dev/null 2>&1 || fail \
    "nvcc is unavailable after loading the CUDA module."
  command -v gcc >/dev/null 2>&1 || fail \
    "gcc is unavailable after loading the CUDA module."

  local cuda_release
  local gcc_version
  local gcc_major
  cuda_release="$(nvcc --version | sed -nE 's/.*release ([0-9]+\.[0-9]+).*/\1/p' | head -n 1)"
  gcc_version="$(gcc -dumpfullversion -dumpversion)"
  gcc_major="${gcc_version%%.*}"

  if [[ "$cuda_release" == "12.2" ]] && \
    [[ "$gcc_major" =~ ^[0-9]+$ ]] && (( gcc_major > 12 )); then
    case " ${NVCC_PREPEND_FLAGS:-} " in
      *" -allow-unsupported-compiler "*) ;;
      *)
        export NVCC_PREPEND_FLAGS="-allow-unsupported-compiler${NVCC_PREPEND_FLAGS:+ $NVCC_PREPEND_FLAGS}"
        ;;
    esac
    printf 'CUDA 12.2 detected with GCC %s; enabling the NVIDIA host-compiler compatibility override.\n' \
      "$gcc_version"
  fi
}

require_slurm_job() {
  [[ -n "${SLURM_JOB_ID:-}" ]] || fail \
    "This helper must run inside a Slurm job. Use the wrapper command from README.md."
}
