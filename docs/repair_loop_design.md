# Repair Loop Design

This document tracks the design evolution of the verifier-guided repair loop in CedarForge.

---

## v1 — Flat Feedback (current implementation)

**Implemented in:** `run_baseline.py` — `_render_failure_feedback()`, `_build_repair_prompt()`

**Mechanism:**
- All stage results (syntax, schema, semantic) are flattened into a single text block
- Raw verifier errors and counterexamples are truncated and concatenated
- The same `repair.md` template is used regardless of which layer failed
- No history is passed across iterations

**Known problems:**
- No error-type prioritization: syntax and semantic errors appear together, confusing the model
- No directional signal: ceiling vs floor failures require opposite fixes; the model cannot tell which direction to move
- No cross-iteration memory: the model cannot detect that it is oscillating or that a previously-passing check has regressed
- Observed result: error oscillation (syntax ↔ semantic cycling) on `max_iterations=10` runs

---

## v2 — Layered, Directional, Memory-Aware Feedback (planned)

**Design principles:**

### 1. Strict layer prioritization

Only surface the highest-priority failing layer. Do not show semantic errors if syntax is still broken.

Priority order: `syntax > schema > semantic`

Rationale: `cedar symcc` is not run on syntactically invalid policies. Semantic counterexamples shown while syntax is broken may be stale or misleading artifacts.

### 2. Error-type-specific repair prompts

Use separate prompt templates for each failure layer:
- `repair_syntax.md`: focus on fixing the specific token/expression; preserve all policy logic
- `repair_schema.md`: identify which entity type, attribute, or action does not exist in the schema
- `repair_semantic.md`: use reference policy + counterexample + directional hint

### 3. Directional hints for semantic failures

For each failing semantic check, include:
- **Direction**: `ceiling` fail → "your policy allows requests that the ceiling forbids — tighten this rule"; `floor` fail → "your policy denies requests that the floor requires — relax this rule"
- **Reference policy**: the full Cedar text of the violated ceiling or floor policy
- **Counterexample**: the specific request that exposed the violation

This reduces the repair task from "re-derive the policy from the spec" to "adjust this rule against this concrete boundary."

### 4. Oscillation detection

Track across iterations:
- `candidate_hash`: SHA of the candidate text. Identical hash = model output is stuck.
- `failure_set`: set of failing check names. Same failure set across iterations = no convergence progress.
- `failure_type_sequence`: list of which layers failed per iteration. Detect syntax → semantic → syntax cycling.

When oscillation is detected, add an explicit warning to the repair prompt:
> "You have been alternating between syntax errors and semantic failures. In your next attempt, ensure syntax is correct first, then address semantic issues. Do not change policy logic while fixing syntax."

### 5. Best-so-far tracking and rollback

Maintain the best candidate seen across all iterations, defined as:
- syntax-passing AND lowest loss (fewest failed semantic checks)

If oscillation is detected, resume repair from the best-so-far candidate rather than the most recent one.

### 6. Escalation stop condition

If oscillation persists for N consecutive iterations with no improvement in loss, stop with `stop_reason="oscillation_no_progress"` and report the best-so-far candidate.

Do not attempt to auto-diagnose whether the verification plan or references are at fault — that requires human review.

---

## Open Questions for v2

- How many iterations of oscillation before triggering the warning? (current tentative: 2 cycles)
- Should the repair prompt include the full iteration history, or only the last N iterations? (context window concern for 9B models)

---

## v2 Implementation Notes

### Temperature split: initial vs repair

**Decision:** Initial generation uses the caller-supplied temperature (default `0.0`). Repair iterations (iteration > 1) use a fixed `REPAIR_TEMPERATURE = 0.4`.

**Why:** At `temperature=0` the model is fully deterministic — the same prompt always produces the same output. This means if the first candidate is wrong, every repair iteration will produce the exact same wrong candidate regardless of what feedback is given. The oscillation detector then triggers immediately (hash collision every iteration) and stops the loop after 6 iterations, making the repair loop completely ineffective.

Setting repair iterations to `0.4` gives the model enough stochasticity to explore different candidates while staying constrained enough to produce coherent Cedar. Values above `0.5` risk introducing hallucinated schema elements on a strongly-constrained generation task like Cedar.

**Observed failure (2026-04-09):** 10 consecutive runs on `clinical_trial` all hit `oscillation_no_progress` at iteration 6 with `failure_layer_sequence = ['syntax', 'syntax', ...]` — the model was outputting the identical syntactically invalid candidate every iteration at `temperature=0`.

---
