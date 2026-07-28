#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

load_config "${1:-}"

if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  fail "Run this check on a Jarvis login node, not inside an existing Slurm job."
fi

for command_name in srun sinfo git curl df awk; do
  command -v "$command_name" >/dev/null 2>&1 || fail \
    "$command_name is unavailable. Are you logged in to a Jarvis login node?"
done

build_cpu_slurm_args
CPU_SLURM_ARGS=("${SLURM_ARGS[@]}")
build_gpu_slurm_args
GPU_SLURM_ARGS=("${SLURM_ARGS[@]}")

printf 'AutoCedar Jarvis preflight\n'
printf '  user: %s\n' "$(whoami)"
printf '  host: %s\n' "$(hostname)"
printf '  CPU partition: %s\n' "$JARVIS_CPU_PARTITION"
printf '  GPU partition: %s\n' "$JARVIS_GPU_PARTITION"
case "$JARVIS_SLURM_ACCOUNT" in
  [Nn][Oo][Nn][Ee])
    printf '  Slurm account: not sent (--account is omitted)\n'
    ;;
  *)
    printf '  Slurm account: %s\n' "$JARVIS_SLURM_ACCOUNT"
    ;;
esac
case "${JARVIS_SLURM_QOS:-none}" in
  [Nn][Oo][Nn][Ee] | "")
    printf '  Slurm QOS: not sent (--qos is omitted)\n'
    ;;
  *)
    printf '  Slurm QOS: %s\n' "$JARVIS_SLURM_QOS"
    ;;
esac

printf '\nChecking that the configured partitions exist...\n'
CPU_PARTITION_INFO="$(sinfo -h -p "$JARVIS_CPU_PARTITION")" || fail \
  "CPU partition '$JARVIS_CPU_PARTITION' is unavailable to this login."
[[ -n "$CPU_PARTITION_INFO" ]] || fail \
  "CPU partition '$JARVIS_CPU_PARTITION' returned no nodes."
GPU_PARTITION_INFO="$(sinfo -h -p "$JARVIS_GPU_PARTITION")" || fail \
  "GPU partition '$JARVIS_GPU_PARTITION' is unavailable to this login."
[[ -n "$GPU_PARTITION_INFO" ]] || fail \
  "GPU partition '$JARVIS_GPU_PARTITION' returned no nodes."

printf 'Checking the CUDA/cuDNN module...\n'
load_gpu_module

printf 'Checking the CPU request without allocating a node...\n'
srun \
  --test-only \
  --job-name=autocedar-preflight-cpu \
  "${CPU_SLURM_ARGS[@]}" \
  true

printf 'Checking the GPU request without allocating a GPU...\n'
srun \
  --test-only \
  --job-name=autocedar-preflight-gpu \
  "${GPU_SLURM_ARGS[@]}" \
  true

configure_huggingface_paths
AVAILABLE_KIB="$(df -Pk "$AUTOCEDAR_MODEL_CACHE" | awk 'NR == 2 {print $4}')"
REQUIRED_KIB=$((50 * 1024 * 1024))
[[ "$AVAILABLE_KIB" =~ ^[0-9]+$ ]] || fail \
  "Could not measure free space at $AUTOCEDAR_MODEL_CACHE."

printf '\nModel cache: %s\n' "$AUTOCEDAR_MODEL_CACHE"
df -h "$AUTOCEDAR_MODEL_CACHE"
if (( AVAILABLE_KIB < REQUIRED_KIB )); then
  fail "The model cache has less than 50 GiB free. Set AUTOCEDAR_MODEL_CACHE in config/jarvis.env to an absolute scratch/project path with at least 50 GiB free."
fi

if command -v quota >/dev/null 2>&1; then
  printf '\nYour reported filesystem quota (if Jarvis exposes it):\n'
  quota -s 2>/dev/null || true
fi

printf '\nPASS: the known Jarvis CPU/GPU requests were accepted without an explicit account or QOS.\n'
printf 'You can continue with the one-time installation steps in README.md.\n'
