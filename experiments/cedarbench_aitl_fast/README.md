# CedarBench AITL Fast GPT-5.5 Low Run

This directory contains a full CedarBench synthesis run used to compare
baseline GPT-5.5 policy synthesis against AutoCedar-style verifier-backed
targets.

## Run

- Run id: `cedarbench-aitl-fast-gpt55-low-20260630`
- Model: `gpt-5.5`
- Effort: `low`
- Mode: fast AITL synthesis over checked-in CedarBench formal targets
- Scenarios: 221
- Converged automatically: 216
- Failed automatically: 5
- Total recorded scenario time: 5,434.74 seconds
- Estimated cost: 8.9441 USD
- Total tokens: 2,007,477

The fast AITL mode uses each CedarBench scenario's `schema.cedarschema`,
`verification_plan.py`, and `references/*.cedar` as the already-reviewed
formal intent target. It then runs the synthesis loop against those targets.
It does not re-run the slow natural-language schema/property atomization path.

## Main Artifacts

- `cedarbench-aitl-fast-gpt55-low-20260630/summary.json`
  machine-readable aggregate metrics.
- `cedarbench-aitl-fast-gpt55-low-20260630/scenario_results.jsonl`
  per-scenario timing, cost, token, iteration, and convergence results.
- `cedarbench-aitl-fast-gpt55-low-20260630/workspaces/<scenario>/`
  per-scenario synthesis workspace.

Each scenario workspace contains:

- `policy_spec.md`
- `schema.cedarschema`
- `verification_plan.py`
- `references/*.cedar`
- `candidate.cedar`
- `eval_log.json`

The `schema.cedarschema`, `verification_plan.py`, and `references/*.cedar`
files are the formal target needed for baseline GPT-5.5 synthesis comparisons.

## Repair Pass

`repair_pass_20260630/` contains agent-inspected repairs for the five automatic
failures. All five verify after inspection.

Breakdown:

- Policy-generation failures repaired by better candidate policies:
  - `if_then_else_decision_tree`
  - `tags_add_owner_bypass`
  - `tags_remove_all_wildcard`
- Target/benchmark-plan issues repaired by target changes:
  - `decoy_trivial_properties`: the original "trivial floors" were not
    actually trivial under floor-implies semantics; `permit when true` as a
    floor requires the candidate to permit every request, contradicting the
    ceiling.
  - `grace_period_three_tier`: the original datetime target was inconsistent
    near Cedar datetime min/max because `datetime.offset(duration(...))` can
    overflow/underflow. The repair adds an explicit realistic certificate
    expiry domain guard.

This distinction matters for reporting: the original automated result is
216/221; with agentic repair and target audit, the benchmark can be made
221/221, but two of the five require benchmark-plan fixes rather than only
better synthesis.

## Reproduction

Run the fast benchmark driver:

```bash
AUTOCEDAR_PROVIDER=codex AUTOCEDAR_HARNESS_EFFORT=low \
uv run python scripts/run_cedarbench_aitl_fast.py \
  --run-id cedarbench-aitl-fast-gpt55-low-YYYYMMDD \
  --model gpt-5.5 \
  --effort low \
  --max-iters 20 \
  --resume
```

The script writes checkpoints after each scenario, so interrupted runs can be
resumed safely with the same `--run-id --resume`.
