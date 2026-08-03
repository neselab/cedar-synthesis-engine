#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

load_config "${1:-}"
build_gpu_slurm_args

command -v sbatch >/dev/null 2>&1 || fail "sbatch is not available; run this command on a Jarvis login node."
command -v squeue >/dev/null 2>&1 || fail "squeue is not available; run this command on a Jarvis login node."
mkdir -m 700 -p "$BUNDLE_ROOT/logs"
chmod 700 "$BUNDLE_ROOT/logs"

submission="$(sbatch \
  --parsable \
  --job-name=autocedar-smoke \
  "${SLURM_ARGS[@]}" \
  --chdir="$BUNDLE_ROOT" \
  --output="$BUNDLE_ROOT/logs/autocedar-smoke-%j.out" \
  "$BUNDLE_ROOT/slurm/autocedar-smoke.sbatch" \
  "$CONFIG_FILE")"

# --parsable prints JOB_ID or JOB_ID;CLUSTER_NAME.
job_id="${submission%%;*}"
[[ "$job_id" =~ ^[0-9]+$ ]] || fail \
  "Slurm accepted the command, but its job number could not be read: $submission"

output_file="$BUNDLE_ROOT/logs/autocedar-smoke-${job_id}.out"
vllm_log="$BUNDLE_ROOT/logs/vllm-${job_id}.log"

printf 'Smoke test submitted as Slurm job %s.\n' "$job_id"
printf 'Waiting for a GPU. Keep this terminal open; waiting in the queue is normal.\n'

last_state=""
while :; do
  # Listing the current user's queue stays successful after this job leaves
  # the queue; querying a completed job ID directly can be an error on some
  # Slurm installations.
  state="$(
    squeue --noheader --user="$USER" --format="%i %T" |
      awk -v wanted="$job_id" '$1 == wanted { print $2; exit }'
  )"
  [[ -n "$state" ]] || break
  if [[ "$state" != "$last_state" ]]; then
    printf 'Job %s status: %s\n' "$job_id" "$state"
    last_state="$state"
  fi
  sleep 10
done

# Slurm may remove the job from squeue just before the output file becomes
# visible on the shared filesystem.
for _ in {1..10}; do
  [[ -f "$output_file" ]] && break
  sleep 1
done
[[ -f "$output_file" ]] || fail \
  "Job $job_id left the queue, but $output_file was not created. Ask for help and include job number $job_id."

printf '\nJob %s finished. Here is its complete output:\n\n' "$job_id"
cat "$output_file"

if grep -q 'Smoke test passed\.' "$output_file"; then
  printf '\nSUCCESS: AutoCedar can talk to the local Qwen model.\n'
else
  printf '\nThe smoke test did not pass. Send both paths below to your supervisor:\n' >&2
  printf '  %s\n  %s\n' "$output_file" "$vllm_log" >&2
  exit 1
fi
