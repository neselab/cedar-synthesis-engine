# CEGIS Algorithm Specification

## Overview

The Cedar Synthesis Engine implements a two-phase Counterexample-Guided Inductive Synthesis (CEGIS) protocol. Phase 1 constructs the verification harness (reference policies + checks). Phase 2 runs the synthesis loop proper: an LLM generates candidate policies, an SMT solver verifies them, and counterexamples guide the next iteration.

## Definitions

| Symbol | Meaning |
|---|---|
| S | Cedar schema (entity types, attributes, actions) |
| R | Set of reference policies {r_1, ..., r_n} (ceilings and floors) |
| V | Verification plan: set of checks {v_1, ..., v_m} |
| C | Candidate Cedar policy (the synthesis target) |
| L | LLM synthesis function |
| O | SMT oracle (CVC5 via `cedar symcc`) |
| cx(v, C) | Counterexample from check v failing on candidate C |

## Phase 1: Verification Harness Construction

```
INPUTS:   S (schema), P (policy spec in natural language)
OUTPUTS:  V (verification plan), R (reference policies)

1.  R, V ← L_phase1(S, P)           // LLM generates references + checks
2.  R, V ← HUMAN_REVIEW(R, V)       // Human approves or provides feedback
    2a. If rejected with feedback f:
        R, V ← L_phase1(S, P, R, V, f)   // Regenerate with feedback
        Go to 2.
3.  Write R to references/*.cedar
4.  Write V to verification_plan.py
```

Phase 1 is executed once per scenario. The human review gate (step 2) ensures reference policy correctness — this is the trust anchor for the entire system (see `soundness_threat_model.md`).

When `--no-review` is set (automated benchmarking), step 2 is skipped.

## Phase 2: CEGIS Synthesis Loop

```
INPUTS:   S (schema), P (policy spec), V (checks), R (references)
OUTPUTS:  C* (verified candidate) or FAILURE

1.  history ← []                      // conversation context
2.  prev_failed ← ∅                   // for oscillation detection
3.  for iteration = 1 to MAX_ITERS:

4.      C ← L_phase2(S, P, V, history)    // LLM generates/fixes candidate

5.      // Gate 1: Syntax
6.      if not SYNTAX_VALID(S, C):
7.          history ← history + [(C, "SYNTAX_ERROR")]
8.          continue

9.      // Gate 2: Verification
10.     results ← []
11.     for each check v_i in V:
12.         result_i ← O(S, C, R, v_i)     // SMT oracle
13.         results ← results + [result_i]

14.     loss ← |{r ∈ results : r.failed}|

15.     // Convergence check
16.     if loss == 0:
17.         return C                         // VERIFIED

18.     // Build feedback signal
19.     failed ← {r.name : r ∈ results, r.failed}
20.     feedback ← FORMAT_FEEDBACK(results, V, R, prev_failed)
21.     prev_failed ← failed
22.     history ← history + [(C, feedback)]

23.     // Context window management
24.     if |history| > TRIM_THRESHOLD:
25.         history ← history[0:1] + history[-KEEP_RECENT:]

26. return FAILURE                          // did not converge
```

## Subroutine: SMT Oracle

The oracle dispatches to different `cedar symcc` subcommands based on check type:

```
O(S, C, R, v):
    match v.type:
        "implies":
            // candidate ≤ ceiling
            return cedar_symcc_implies(S, C, v.reference, v.scope)

        "floor":
            // floor ≤ candidate (reversed implies)
            return cedar_symcc_implies(S, v.floor, C, v.scope)

        "always-denies-liveness":
            // NOT always-denies (inverted)
            raw ← cedar_symcc_always_denies(S, C, v.scope)
            return invert(raw)

        "never-errors":
            return cedar_symcc_never_errors(S, C, v.scope)

    where v.scope = (v.principal_type, v.action, v.resource_type)
```

Each call returns `(passed: bool, counterexample: string)`. The oracle is **sound and complete** — see `decidability.md`.

## Subroutine: Feedback Signal

See `feedback_signal_design.md` for the full specification. Summary:

```
FORMAT_FEEDBACK(results, V, R, prev_failed):
    1. Detect oscillation:
       fixed     ← prev_failed - current_failed
       regressed ← current_failed - prev_failed
       if fixed ≠ ∅ and regressed ≠ ∅:
           emit oscillation warning

    2. For each failed check:
       - Include directional explanation (too permissive / too restrictive)
       - Include the reference policy source (ceiling or floor Cedar code)
       - Include the raw counterexample

    3. Instruction: fix all failures without breaking passing checks
```

## Subroutine: Context Window Management

The LLM conversation accumulates context with each iteration. To stay within context limits:

```
TRIM_THRESHOLD = 12 messages
KEEP_RECENT    = 8 messages

if |history| > TRIM_THRESHOLD:
    history ← [history[0]] + history[-KEEP_RECENT:]
```

The first message (containing schema, spec, and check descriptions) is always preserved. This ensures the model retains the problem definition even as older iterations are evicted.

## Termination and Convergence

**Termination.** The loop always terminates: it is bounded by `MAX_ITERS` (default 20). Each verification step terminates because Cedar verification is decidable (see `decidability.md`). Each LLM call terminates because API calls have finite `max_tokens`.

**Convergence.** The loop converges (reaches loss = 0) when the LLM produces a candidate that satisfies all checks simultaneously. Convergence is not guaranteed — it depends on:

1. **Model capability.** Stronger models converge faster (Sonnet: 1-5 iterations, Haiku: 2-10 on easy scenarios, may not converge on hard ones with baseline feedback).
2. **Feedback quality.** Rich feedback (reference policies + directional explanation + oscillation detection) significantly improves convergence for weaker models.
3. **Scenario complexity.** More checks, tighter ceiling-floor gaps, and forbid/unless interactions increase difficulty.
4. **Context window.** The trimming strategy may evict useful context on long runs.

## Loss as a Metric

Loss is defined as the count of failed checks:

```
loss(C, V) = |{v ∈ V : O(S, C, R, v).failed}|
```

Loss is:
- **Non-negative**: loss ∈ {0, 1, ..., |V|}
- **Zero at convergence**: loss = 0 ↔ all checks pass ↔ policy is verified
- **Not necessarily monotonically decreasing**: the model may regress (oscillation)

The loss curve over iterations characterizes synthesis difficulty. A monotonically decreasing curve indicates the model is making consistent progress. An oscillating curve indicates the model is struggling with simultaneous constraint satisfaction.

## Implementation Mapping

| Algorithm component | Implementation |
|---|---|
| L_phase1 | `generate_references()` in `eval_harness.py` |
| HUMAN_REVIEW | `review_references()` in `eval_harness.py` |
| L_phase2 | Anthropic API call with `PHASE2_SYSTEM` prompt |
| O (oracle) | `run_verification()` in `orchestrator.py` |
| SYNTAX_VALID | `run_syntax_check()` in `solver_wrapper.py` |
| FORMAT_FEEDBACK | `_format_feedback()` in `eval_harness.py` |
| Context trim | Inline in `run_scenario()` CEGIS loop |
| Loss computation | `VerificationResult.loss` in `solver_wrapper.py` |
