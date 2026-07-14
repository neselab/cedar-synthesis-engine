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

require_slurm_job() {
  [[ -n "${SLURM_JOB_ID:-}" ]] || fail \
    "This helper must run inside a Slurm job. Use the wrapper command from README.md."
}
