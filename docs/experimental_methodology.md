# Experimental Methodology

## Research Questions

The evaluation harness is designed to answer:

1. **RQ1 (Feasibility):** Can LLMs synthesize formally verified Cedar policies via CEGIS?
2. **RQ2 (Model scaling):** How does synthesis performance vary across model capability levels?
3. **RQ3 (Feedback signal):** Does richer verification feedback improve convergence for weaker models?
4. **RQ4 (Scenario complexity):** What structural properties of a scenario predict synthesis difficulty?

## Independent Variables

| Variable | Values | How to set |
|---|---|---|
| Phase 2 model | Opus, Sonnet, Haiku (or any Anthropic model) | `--phase2-model` |
| Phase 1 model | Typically fixed to a strong model | `--phase1-model` |
| Feedback signal | Baseline vs. revamped (code change) | Code-level; see `feedback_signal_design.md` |
| Scenario | experiments/github, workspace, dataset/* | `--scenario` |
| Reference source | Pre-existing (human-written) vs. LLM-generated | `--gen-references` |
| Max iterations | Default 20 | `--max-iters` |

## Dependent Variables (Metrics)

All metrics are logged per-iteration in `eval_log.json` and aggregated in `summary.json`.

### Primary metrics

| Metric | Definition | Logged as |
|---|---|---|
| **Converged** | Did loss reach 0 within max iterations? | `converged: bool` |
| **Iterations to convergence** | Number of CEGIS iterations before loss = 0 | `iterations: int` |
| **Final loss** | Loss at the last iteration (0 if converged) | `final_loss: int` |

### Per-iteration metrics

| Metric | Definition | Logged as |
|---|---|---|
| **Loss** | Count of failed checks | `iteration_log[i].loss` |
| **Checks passed** | Count of passing checks | `iteration_log[i].checks_passed` |
| **Solver time** | Wall-clock time for all SMT queries in this iteration | `iteration_log[i].solver_time_s` |
| **Counterexample count** | Number of checks that produced counterexamples | `iteration_log[i].counterexample_count` |
| **Syntax valid** | Did the candidate pass `cedar validate`? | `iteration_log[i].syntax_valid` |
| **Status** | Classification: `pass`, `fail`, `syntax_error`, `llm_error` | `iteration_log[i].status` |

### Aggregate metrics

| Metric | Definition | Logged as |
|---|---|---|
| **Total time** | Wall-clock time for entire scenario (Phase 1 + review + Phase 2) | `total_time_s` |
| **Phase 1 time** | Time for reference generation (0 if using pre-existing) | `phase1_time_s` |
| **Phase 2 time** | Time for CEGIS loop | `phase2_time_s` |
| **Checks total** | Number of checks in the verification plan | `checks_total` |

## Experimental Protocols

### Protocol A: Model comparison (RQ1, RQ2)

Hold the scenario and references fixed, vary the Phase 2 model.

```bash
python eval_harness.py \
    --scenario experiments/github workspace \
    --phase1-model claude-sonnet-4-20250514 \
    --phase2-model claude-sonnet-4-20250514 claude-haiku-4-5-20251001 \
    --no-review --max-iters 20 \
    --run-id model_comparison
```

This uses pre-existing (human-reviewed) references for both scenarios, so the only variable is the Phase 2 synthesis model. Each (scenario, model) pair produces an independent eval_log.

### Protocol B: Feedback ablation (RQ3)

Compare baseline vs. revamped feedback on the same model and scenario. This requires running the harness twice with different code versions (or a feature flag).

```bash
# Revamped feedback (current code)
python eval_harness.py --scenario workspace \
    --phase2-model claude-haiku-4-5-20251001 \
    --no-review --run-id feedback_revamped

# Baseline feedback (revert _format_feedback to baseline)
python eval_harness.py --scenario workspace \
    --phase2-model claude-haiku-4-5-20251001 \
    --no-review --run-id feedback_baseline
```

### Protocol C: End-to-end with Phase 1 generation (RQ1)

Test the full pipeline including LLM-generated references.

```bash
python eval_harness.py \
    --scenario experiments/github \
    --phase1-model claude-sonnet-4-20250514 \
    --phase2-model claude-sonnet-4-20250514 \
    --gen-references --no-review \
    --run-id e2e_generated_refs
```

### Protocol D: Scenario sweep (RQ4)

Run all available scenarios to characterize difficulty.

```bash
python eval_harness.py --all \
    --phase2-model claude-sonnet-4-20250514 \
    --gen-references --no-review --max-iters 20 \
    --run-id scenario_sweep
```

Note: dataset scenarios require `--gen-references` since they lack verification plans. They also lack `policy_spec.md`, which must be added before running.

## Reproducibility

### Run isolation

Each run creates an isolated workspace under `eval_runs/{run_id}/{scenario_name}/` with copies of all scenario files. The original scenario files are never modified. This means:

- Multiple runs can execute in parallel without interference
- Each run is self-contained and can be inspected after the fact
- The candidate policy from each iteration is overwritten (only the final candidate is preserved)

### Non-determinism

LLM outputs are non-deterministic (temperature > 0 by default in the Anthropic API). This means:

- Two runs with identical parameters may produce different iteration counts
- Statistical significance requires multiple runs per configuration
- The eval harness does not currently support multi-trial runs natively; use different `--run-id` values and aggregate externally

### Output structure

```
eval_runs/
├── {run_id}/
│   ├── summary.json              # Aggregate results for all scenarios
│   ├── {scenario_name}/
│   │   ├── schema.cedarschema    # Copied from source
│   │   ├── policy_spec.md        # Copied from source
│   │   ├── verification_plan.py  # Copied or generated
│   │   ├── references/           # Copied or generated
│   │   ├── candidate.cedar       # Final candidate (last iteration)
│   │   ├── policy_store.cedar    # Verified policies appended here
│   │   └── eval_log.json         # Per-scenario detailed log
│   └── ...
```

### Key fields in summary.json

```json
{
    "run_id": "model_comparison",
    "phase1_model": "claude-sonnet-4-20250514",
    "phase2_models": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
    "max_iterations": 20,
    "gen_references": false,
    "human_review": false,
    "timestamp": "2026-04-03T02:13:14Z",
    "results": [...]
}
```

## Reporting Conventions

When reporting results, include:

1. **Model identifiers.** Full model ID (e.g., `claude-sonnet-4-20250514`), not just family name.
2. **Reference source.** Whether references were pre-existing (human-written) or LLM-generated.
3. **Review status.** Whether human review was performed (`human_review` field).
4. **Feedback variant.** Baseline or revamped (if comparing feedback signals).
5. **Iteration limit.** The `max_iterations` setting.
6. **Number of trials.** If reporting statistics, how many independent runs per configuration.

### Suggested results table format

| Scenario | Phase 2 Model | Refs | Feedback | Converged | Iters | Time |
|---|---|---|---|---|---|---|
| github | Sonnet | pre-existing | revamped | Yes | 1 | 5.5s |
| github | Haiku | pre-existing | revamped | Yes | 2 | 6.8s |
| workspace | Sonnet | pre-existing | revamped | Yes | 5 | 20.0s |
| workspace | Haiku | pre-existing | baseline | No (10/10) | 10 | 60.3s |
| workspace | Haiku | pre-existing | revamped | Yes | 2 | 5.4s |

### Loss curve visualization

The `iteration_log` array in `eval_log.json` supports plotting loss over iterations. A useful visualization is a step plot of `loss` vs. `iteration` for each (scenario, model, feedback) configuration, showing convergence behavior and oscillation patterns.
