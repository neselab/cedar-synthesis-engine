# Single-Model Baselines

This folder defines the first experimental matrix for Cedar policy generation.

The purpose is to establish a clean baseline before adding multi-agent coordination.

This directory now also includes a verifier-guided repair mode in the same runner so you can measure whether a single model improves across multiple iterations after seeing formal feedback.

## Experimental Matrix

The current prompt variants are:

- `zero_shot_direct`
  Measure the raw ability of the model to generate a Cedar policy from the task description.

- `structured_instruction`
  Add explicit constraints, output rules, and task decomposition guidance.

- `cot`
  Encourage stepwise internal reasoning about policy construction before producing the final answer.

- `few_shot_grounded`
  Provide a grounded positive example so the model can imitate a correct Cedar pattern.

Each prompt strategy is stored as its own file under:

- [prompt_strategies/](prompt_strategies)

This makes it easy to:

- edit one strategy without touching the others
- run one strategy at a time with `--variant`
- compare prompt revisions cleanly with git

## Evaluation Criteria

- syntax correctness:
  `cedar validate`

- semantic alignment:
  symbolic verification via ceiling/floor/liveness checks

## Metrics

The reusable metric code lives under:

- [../../metrics/policy_generation_metrics.py](../../metrics/policy_generation_metrics.py)
- [../../metrics/policy_generation_evaluator.py](../../metrics/policy_generation_evaluator.py)

The current metrics are:

- `SyntaxPass`
  Whether the candidate is parsable Cedar.

- `SchemaPass`
  Whether the candidate grounds correctly against the provided schema.

- `SemanticAccuracy`
  Fraction of formal verification checks passed after syntax and schema validation succeed.

At the prompt-strategy summary level, the main reported metrics are:

- `SyntaxPassRate`
- `SchemaPassRate`
- `SemanticAccuracy`

Lower-level diagnostic fields still exist in the per-run record for future error analysis, but they are not part of the main experiment table.

## Initial Task Registry

Currently registered tasks include:

- `github`
  backed by `/experiments/github` in the parent repo

- `clinical_trial`
  backed by `cedarforge/dataset/clinical_trial`

The GitHub task is a strong first benchmark because it includes:

- upper bounds
- lower bounds
- liveness constraints
- multi-path authorization logic

## Running

Activate the `vllm` environment first, then run from the repo root:

```bash
conda activate vllm
cd /home/yzhou136/cedar-synthesis-engine
CVC5=$CONDA_PREFIX/bin/cvc5 python cedarforge/src/experiments/single_model_baselines/run_baseline.py \
  --task github \
  --variant structured_instruction \
  --base-url http://localhost:8002/v1 \
  --model qwen35b
```

Run all prompt variants for one task:

```bash
conda activate vllm
cd /home/yzhou136/cedar-synthesis-engine
CVC5=$CONDA_PREFIX/bin/cvc5 python cedarforge/src/experiments/single_model_baselines/run_baseline.py \
  --task github \
  --all-variants \
  --base-url http://localhost:8002/v1 \
  --model qwen35b
```

Run a verifier-guided repair loop from the same entrypoint:

```bash
conda activate vllm
cd /home/yzhou136/cedar-synthesis-engine
CVC5=$CONDA_PREFIX/bin/cvc5 python cedarforge/src/experiments/single_model_baselines/run_baseline.py \
  --task github \
  --mode repair \
  --variant structured_instruction \
  --base-url http://localhost:8002/v1 \
  --model qwen35b \
  --max-iterations 4
```

## Output

Each run writes to `cedarforge/src/experiments/single_model_baselines/runs/<run_id>/`.

Artifacts include:

- prompt text
- raw model output
- extracted candidate policy
- evaluation bundle JSON
- verification result JSON
- run log
- run summary JSON

Task assets such as:

- Cedar schema
- policy specification
- references
- verification plan

are not copied into the visible run output. The runner uses a hidden internal evaluation workspace that links back to the original task files.
By default, that internal workspace is deleted after evaluation.

If you want to keep it for debugging, add:

```bash
--keep-eval-workspace
```

Repair loop runs write one subdirectory per iteration and add per-iteration rollups in `summary.json`.

To print a prompt-strategy summary from a finished run:

```bash
python cedarforge/src/metrics/summarize_prompt_strategies.py \
  cedarforge/src/experiments/single_model_baselines/runs/<run_id>/summary.json
```

To evaluate any prepared workspace directly:

```bash
conda activate vllm
cd /home/yzhou136/cedar-synthesis-engine
CVC5=$CONDA_PREFIX/bin/cvc5 python cedarforge/src/metrics/evaluate_workspace.py \
  experiments/github \
  --prompt-variant manual_check
```

## Runtime Behavior

When you run a baseline, the runner now prints:

- which strategy is running
- the full prompt
- the raw model output
- the extracted Cedar candidate
- stage-by-stage evaluation results for:
  - syntax
  - schema
  - semantic

For the semantic stage, the runner also prints:

- each verification check name
- check type
- pass/fail
- description
- counterexample summary when a check fails

For syntax and schema failures, the runner also prints:

- a short human-readable explanation
- likely cause
- suggested fix

The evaluation is sequential:

1. syntax
2. schema
3. semantic

If a lower-level stage fails, higher-level stages are skipped.
