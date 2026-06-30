# CedarBench AITL Fast GPT-5.5 Low Run

Artifact directory for the CedarBench GPT-5.5 low-effort synthesis run.

## Contents

- `cedarbench-aitl-fast-gpt55-low-20260630/`
  - `summary.json`
  - `SUMMARY.md`
  - `scenario_results.jsonl`
  - `manifest.json`
  - `workspaces/<scenario>/`
- `repair_pass_20260630/`
  - final inspected workspaces used by the completed artifact package

Each scenario workspace includes the files needed for synthesis comparison:

- `policy_spec.md`
- `schema.cedarschema`
- `verification_plan.py`
- `references/*.cedar`
- `candidate.cedar`
- `eval_log.json`

## Reproduction

```bash
AUTOCEDAR_PROVIDER=codex AUTOCEDAR_HARNESS_EFFORT=low \
uv run python scripts/run_cedarbench_aitl_fast.py \
  --run-id cedarbench-aitl-fast-gpt55-low-YYYYMMDD \
  --model gpt-5.5 \
  --effort low \
  --max-iters 20 \
  --resume
```
