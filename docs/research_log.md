# CedarForge Research Log

Chronological record of research progress, design decisions, and empirical observations.
This log is intended as a reference for paper writing.

---

## 2026-04-04 — Project Motivation and Initial Framing

**Context:**
Frontier models (Claude, GPT-4, etc.) can already generate Cedar policies from natural-language specs and iterate on verifier feedback. This has been demonstrated in the parent `cedar-synthesis-engine` repo using the CEGIS loop with Claude.

**Core problem identified:**
Large enterprises (AWS, Google, etc.) often cannot send internal access-control specifications, schemas, or policy logic to public hosted frontier models due to security and compliance constraints.

**Research question:**
Can open-source small models, when surrounded by a strong system (structured prompts, formal verification, iterative repair), approach the performance of frontier models on Cedar policy generation?

**Working hypothesis:**
Small models will not match frontier models in raw one-shot synthesis. But they may close the gap if the system provides:
- task decomposition
- retrieval of reference patterns
- structured verifier feedback
- counterexample-guided repair
- oscillation detection

**Planned research stages:**
1. Single-model baselines — establish the capability boundary of a single open-source model under various prompt strategies
2. Verifier-guided repair loop — measure whether structured feedback improves convergence
3. Multi-agent system — split planning and grounding into separate agents with explicit roles

---

## 2026-04-07 — Stage 1: Single-Model Baseline Runs

**What was built:**
- Evaluation pipeline with three layers: syntax → schema → semantic
- Four prompt strategies: `zero_shot_direct`, `structured_instruction`, `cot`, `few_shot_grounded`
- Two benchmark tasks: `clinical_trial`, `github_repo_permission`
- Automated matrix runner (`run_matrix.sh`) over tasks × variants × modes

**Models tested:**
- Qwen 35B (vLLM endpoint)
- Qwen 27B
- Qwen 9B

**Key observation — syntax failures:**
Zero-shot and unguided prompts consistently produced syntax errors. The most common failure pattern was incorrect `when`-clause attachment (e.g., `unexpected token {`). This suggests the models have partial but unreliable Cedar syntax knowledge.

**Key observation — prompt strategy ranking:**
`structured_instruction` showed stronger syntax pass rates than `zero_shot_direct` and `cot` across both tasks. The explicit cheat sheet and schema-grounding instructions appear to reduce surface-level syntax errors.

**Decision:**
Proceed with `structured_instruction` as the fixed prompt strategy for the repair loop experiments, rather than continuing to compare all four strategies in repair mode.

---

## 2026-04-09 — Repair Loop v1: Design and Observed Failures

**What was built:**
- `run_repair_loop()` in `run_baseline.py`
- `_render_failure_feedback()`: formats verifier output as flat text
- `repair.md`: prompt template for repair iterations
- Per-iteration artifact logging (prompt, candidate, evaluation bundle, verification result)

**Repair loop v1 mechanism:**
1. Generate initial candidate with `structured_instruction` prompt
2. Evaluate against syntax → schema → semantic pipeline
3. If failed: render all stage errors into a flat feedback string; build repair prompt with previous candidate + feedback; call model again
4. Repeat up to `max_iterations`

**Observed failure mode — error oscillation:**
In runs with `max_iterations=10`, the repair loop exhibited error oscillation: the failure type cycled between syntax and semantic across iterations without converging. Example pattern observed:

```
iter 1: syntax=FAIL
iter 2: syntax=PASS, semantic=FAIL (3 checks)
iter 3: syntax=FAIL
iter 4: syntax=PASS, semantic=FAIL (2 checks)
iter 5: syntax=FAIL
...
```

**Root cause analysis:**
The current `_render_failure_feedback()` has three structural problems:

1. **No error-type prioritization.** All stages (syntax, schema, semantic) are rendered together regardless of which layer actually blocked verification. When syntax fails, the semantic counterexamples shown are not grounded in a valid policy and may be misleading.

2. **No directional signal for semantic failures.** A ceiling check failure means the candidate is *too permissive*; a floor check failure means the candidate is *too restrictive*. The current feedback does not communicate this direction. The model has to infer it from raw counterexamples alone.

3. **No cross-iteration memory.** The feedback is constructed only from the most recent `bundle`. The model has no visibility into what changed between iterations, which checks regressed, or whether it has been oscillating.

**Decision:**
Design repair loop v2 with layered feedback, directional semantic hints, and oscillation detection.

---
