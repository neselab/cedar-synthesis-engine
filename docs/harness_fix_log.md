# Harness Fixes for LLM-Driven Cedar Policy Synthesis
*A Chronological Record Reformatted as a System Paper*

## Abstract

We describe the evolution of an evaluation and feedback harness for a two-phase CEGIS (Counterexample-Guided Inductive Synthesis) loop that synthesizes Cedar access-control policies from natural-language specifications. Phase 1 (planner, Opus) decomposes a specification into a verification plan and reference policies; Phase 2 (synthesizer, Haiku) iteratively proposes candidates that are checked by a symbolic verifier (`cedar symcc`) and a type-checker (`cedar validate`). We document seven categories of fixes made during development, culminating in four novel contributions that materially changed convergence behavior: directional feedback signaling, hash-based cross-gate oscillation detection, a Phase 1.25 reference self-validation gate, and a parse-vs-type-check error bifurcation. On the `opus_planner_full` benchmark, scenarios that plateaued at 0/24 iterations under the original harness converged in 4–5 iterations with the full fix set.

## 1. Introduction

A CEGIS loop only converges if the counterexample feedback carries enough signal for the candidate generator to make directed progress. Early iterations of our harness exposed three failure modes that are invisible from loss curves alone: (i) the model cannot tell whether to tighten or loosen; (ii) the model cycles between mutually exclusive gate categories without noticing; and (iii) the planner's own outputs are occasionally unloadable, so every downstream check is garbage. The fixes below address each mode, but the harness also accumulated a larger set of correctness and ergonomic fixes that we document here for completeness.

## 2. System Overview

The harness consists of three layers:

1. **Verification substrate** (`solver_wrapper.py`, `orchestrator.py`): invokes `cedar validate` and `cedar symcc` and returns `VerificationResult` objects containing per-check `CheckResult` records.
2. **Signal layer** (`eval_harness.py::_format_feedback` and adjacent helpers): translates verification failures into natural-language guidance for the model.
3. **Control loop** (`eval_harness.py::run_scenario`): sequences Phase 1, an optional human review gate, Phase 1.25 self-validation, and Phase 2 iterative synthesis.

## 3. Verification Substrate Fixes

### 3.1 Liveness inversion
Liveness checks use `expect_denies=False` to assert that at least one scenario must be permitted. The original pipeline reported the raw symbolic result, which inverted the pass/fail label — a correctly permitted scenario was scored as failing. Fix: `passed = not passed_raw` in the orchestrator when `expect_denies=False`.

### 3.2 Cedar CLI rebuild with `analyze` feature
The packaged `cedar` binary did not expose the `symcc` subcommand. We rebuilt Cedar from source at `/private/tmp/cedar/target/release/cedar` with `--features analyze`. `solver_wrapper.py::CEDAR_PATH` pins this binary for all downstream calls.

### 3.3 Parse-vs-type-check error bifurcation *(novel, §8.4)*
`cedar validate` emits returncode 1 for grammar errors and returncode 3 for type-checker rejections. Both were originally collapsed into a single `"syntax"` check, so unguarded-optional-attribute errors produced feedback instructing the model to "fix parse errors." Fix: `run_syntax_check` now returns `(is_valid, error_msg, error_kind)` with `error_kind ∈ {"", "parse", "validation", "other"}`, and `orchestrator.py::run_verification` routes returncode 3 to `CheckResult(check_type="validation")`.

## 4. Signal Layer Fixes

### 4.1 Structured Cedar error deduplication
`cedar validate` repeats the same error message once per (rule × constraint) pair. A 16-rule policy with two type constraints per rule produces 32 repetitions of the same line, inflating the feedback payload to ~18 kB. `_format_syntax_feedback` parses Cedar's `× / ╰─▶ / help:` box-drawing output, deduplicates by message, keeps the first code snippet per unique error, and emits `**N occurrences of:** <msg>`. Reduces feedback to roughly 500 characters while preserving all distinct information.

### 4.2 Directional feedback signaling *(novel, §8.1)*
An `implies` (ceiling) failure and a `floor` (liveness lower bound) failure are indistinguishable from a raw counterexample; yet the remediation direction is opposite. The original harness passed through "counterexample exists" without annotation. `_format_feedback` now branches on `check_type`:

- **`implies`**: "Your policy is MORE permissive than the ceiling. It allows something the ceiling forbids. Tighten conditions."
- **`floor`**: "Your policy is MORE restrictive than the floor. It denies something that MUST be allowed. Loosen conditions."
- **`liveness`**: "Your policy denies ALL requests for this action. At least one scenario must be permitted."
- **`syntax`**: "SYNTAX / PARSE ERROR — your policy failed to parse. No semantic checks can run until syntax is valid."
- **`validation`**: delegated to `_format_validation_feedback` (§4.6).

Each directional branch inlines the reference or floor Cedar source from disk into the feedback message, so the model sees the literal bound it is being compared against.

### 4.3 Reference policy inlining
Part of §4.2. Instead of referring to a filesystem path (`references/role_check.cedar`), the formatter reads the file and inlines its contents in a fenced block. The token cost is small (tens of tokens per iteration) and eliminates an entire class of "unknown bound" failures.

### 4.4 Set-based oscillation detection
Phase 2 originally could cycle indefinitely between complementary failure sets (fix A, break B, fix B by reverting A). `_format_feedback` receives the previous iteration's `failed: set[str]` and compares against the current set:

```
WARNING - OSCILLATION DETECTED
You fixed: role_check
But broke: approval_floor
ALL checks must pass simultaneously.
Do not sacrifice one bound to satisfy another.
```

This is a soft signal that fires on single-iteration regressions.

### 4.5 Hash-based cross-gate oscillation detection *(novel, §8.2)*
Set-based detection misses a subtler loop: cycling between gate *categories* (syntax → validation → semantic → syntax) with byte-identical candidates each round. `run_scenario` maintains `seen_hashes: dict[str, tuple[int, list[str]]]` keyed by `sha256(candidate_text)`, and `failure_history: list[set[str]]`. When a hash recurs, the harness builds:

```python
repeat_info = {
    "first_iter": <iteration of prior occurrence>,
    "current_failed": <current failure set>,
    "window_union": <union of all failure modes across the loop window>,
}
```

`_format_feedback` then emits the strongest warning in the signal layer — a header instructing the model that it has submitted a byte-identical policy, followed by the union of all failure modes seen during the loop, and an explicit instruction to reason about the conjunction of constraints. Hash detection suppresses the softer §4.4 warning when both would fire.

### 4.6 Validation-error feedback with optional-attribute templates
`_format_validation_feedback` is the twin of `_format_syntax_feedback` for returncode 3. Its first line is a load-bearing disclaimer:

> "This is NOT a parse error. Do NOT change `principal is User` or rule structure."

The previous bug was the synthesizer ripping out its policy header in response to a type-check error because all feedback was labeled "syntax." The formatter then runs a multi-line-safe regex (`r"optional\s+attribute\s+`([^`]+)`"`) to extract the offending attribute names — Cedar wraps long messages, so a single-line regex misses the common case — and emits a targeted CORRECT/WRONG pair using the extracted names:

```cedar
// CORRECT
context has targetUser && context.targetUser.role == "X"
// WRONG
context.targetUser.role == "X"   // unsafe — attribute may be absent
```

The raw validator output is truncated to 1200 characters and appended so the model retains line numbers.

## 5. Control Loop Fixes

### 5.1 Per-phase model selection
`--phase1-model` and `--phase2-model` CLI flags, stored separately in `ScenarioResult` and printed in the scenario header. Defaults: Opus 4.6 for Phase 1 (heavy schema-understanding and ceiling/floor design), Haiku 4.5 for Phase 2 iterative synthesis.

### 5.2 Property-based verification plan decomposition
Early Phase 1 produced a role-split plan (one reference per role), which is not compositional — a per-role ceiling cannot bound the union of behaviors. The current `PHASE1_SYSTEM` prompt instructs Opus to emit *property-based* checks (e.g., "target must be same org," "approver role must be ≥ manager"), each an `implies` against a narrow reference policy. Bounds compose via conjunction.

### 5.3 Phase 1.5 human review gate
Optional (`--no-review` skips). Pauses after Phase 1 so a reviewer can flag bad references and trigger regeneration. Phase 1.25 self-validation runs after each reviewer-driven regeneration.

### 5.4 Phase 1.25 reference self-validation gate *(novel, §8.3)*
The planner was found to emit references containing a specific anti-pattern:

```cedar
!(context has targetUser) || context.targetUser.role == "X"
```

Cedar's type-checker does not propagate negation through `has`, so this is rejected even though it is logically sound. With the reference unloadable, every downstream `implies` / `floor` check failed with an irrelevant error and Phase 2 had no recourse. On the `opus_planner_full` benchmark, 3/8 scenarios had at least two broken references.

`self_validate_references(client, model, workspace, schema, policy_spec, plan_data, max_rounds=3)` runs `cedar validate` on every file in `references/`, and on any rejection calls `generate_references` up to three rounds with `_format_phase1_validation_feedback`, which contains each broken file's content, its exact Cedar error, and a tailored rewrite template:

```cedar
// CORRECT guard form
(!(context has targetUser) || (context has targetUser && context.targetUser.role == "X"))
```

The gate is wired into three sites in `run_scenario`: after fresh generation in the `gen_references` branch; in the "existing verification plan" branch (to auto-heal legacy workspaces); and after each Phase 1.5 reviewer-driven regeneration. After the fix, the three previously-broken scenarios converged in 4, 5, and 5 iterations respectively.

### 5.5 PHASE1_SYSTEM gotchas section
To prevent Phase 1.25 from firing in the common case, `PHASE1_SYSTEM` contains an explicit "Cedar gotchas" block documenting: (i) the negated-`has` trap with CORRECT/WRONG examples; (ii) `is` (not `:`) for type constraints in policy heads; (iii) optional attributes declared with `?` in the schema must be `has`-guarded before read.

### 5.6 Workspace isolation
`setup_workspace` copies the scenario into `run_dir/scenario_name/` so concurrent runs do not collide on `references/` or `candidate.cedar`. A latent `shutil.SameFileError` occurred when the input scenario already lived under `eval_runs/`; fixed by resolving absolute paths before the copy.

### 5.7 `_load_plan_data_from_workspace` fallback
In the "Using existing verification plan" branch, `plan_data` is `None` at entry. If the workspace has broken references that require Phase 1.25 to run, this helper reconstructs `plan_data` from `verification_plan.py` and `references/*.cedar` on disk so the self-correction loop can proceed.

### 5.8 Verified policy auto-append
On Phase 2 convergence, the verified candidate is appended to a running `policy_store.cedar` with a provenance header, enabling an accumulated library across runs.

### 5.9 `--workspace` flag
Re-run a single scenario in a named workspace without regenerating Phase 1 — intended for Phase 2 iteration during harness development.

## 6. Context Management

### 6.1 Conversation trimming
The Phase 2 iterative loop preserves the first message (system + initial user turn) and the last 8 turns, dropping earlier exchanges. Long runs (20+ iterations) no longer exhaust the context window, while the most recent feedback remains visible.

## 7. Debug Instrumentation

### 7.1 `CEDAR_DEBUG=1` syntax-check tracing
When the environment variable is set, `run_syntax_check` writes a per-workspace `_syntax_debug.log` containing the cedar binary path, sha256 of the candidate file, returncode, stdout, and stderr. This instrumentation made the parse-vs-type-check distinction (§3.3) visible in the first place — the two error classes were indistinguishable without it.

## 8. Novel Contributions

Four contributions are, to our knowledge, not present in the standard CEGIS-for-policy literature. Each addresses a concrete, reproducible failure mode observed in the harness.

### 8.1 Directional feedback signaling with inlined reference policies
**Problem addressed:** `implies` and `floor` failures require opposite remediation; raw counterexamples do not encode direction.
**Mechanism:** Per-`check_type` branches in `_format_feedback` emit explicit "MORE permissive than the ceiling / MORE restrictive than the floor" framing and inline the reference or floor Cedar source alongside the counterexample.
**Effect:** Eliminates a class of fix-break-fix cycles in which the synthesizer chases one bound at the cost of another because it cannot distinguish the type of violation.

### 8.2 Hash-based cross-gate oscillation detection
**Problem addressed:** When a synthesizer cycles between gate categories (syntax / validation / semantic), set-based "fixed X, broke Y" detection misses byte-identical resubmissions because the set difference is empty within any single category.
**Mechanism:** Per-iteration sha256 of candidate text; on recurrence, build a `repeat_info` containing `first_iter`, `current_failed`, and the union of all failure modes seen during the loop window; emit a maximally explicit "REPEATED POLICY DETECTED" warning instructing the model to solve the conjunction rather than each gate independently.
**Effect:** Catches loops that span gate categories — invisible to any single-gate loss tracker.

### 8.3 Phase 1.25 reference self-validation gate
**Problem addressed:** Planner LLMs emit reference policies that pass grammar but are rejected by the type-checker, most commonly the negated-`has` anti-pattern. When the reference is unloadable, every downstream semantic check is meaningless, and the synthesizer has no recourse because the signal it receives is decoupled from the true bound.
**Mechanism:** After Phase 1 (and after every regeneration path), run `cedar validate` on every file in `references/`. On any rejection, call `generate_references` up to three rounds with a validation-feedback prompt containing the broken file, the exact Cedar error, and a CORRECT/WRONG rewrite template. Integrate as a separate gate (Phase 1.25) rather than folding into Phase 1 so it can auto-heal pre-existing workspaces and reviewer-driven regenerations uniformly.
**Effect:** On the `opus_planner_full` benchmark, 3/8 scenarios with broken references (previously plateaued) converged in 4, 5, and 5 iterations respectively.

### 8.4 Parse-vs-type-check error bifurcation in CEGIS feedback
**Problem addressed:** Most Cedar tooling surfaces validator output under a single "error" category. A CEGIS loop that reuses the same feedback template for grammar errors and type-checker rejections will deliver actively misleading guidance for the latter — most notably, it will instruct the model to "fix the parse error" when the real issue is an unguarded optional attribute, prompting the model to mangle its (correct) rule header.
**Mechanism:** Returncode-based discrimination in `run_syntax_check`, a separate `CheckResult(check_type="validation")` in the orchestrator, and a dedicated `_format_validation_feedback` formatter whose first line is an explicit disclaimer that this is not a parse error, followed by a multi-line-aware regex that extracts offending optional-attribute names and emits a targeted CORRECT/WRONG template.
**Effect:** On `sales_add_approval`, previously stuck at 0/24 iterations with the synthesizer repeatedly editing its header in response to mislabeled type-check errors, the fix alone (before §8.3 was added) brought the scenario to a 22/24 plateau; combined with §8.3 it converges in 5 iterations.

## 9. Summary

The harness's signal layer is now a structured translator rather than a passthrough: it distinguishes error classes at the source (§3.3), labels each semantic failure with its remediation direction (§4.2), inlines bounds so the model can see what it is being compared against (§4.3), detects loops at two granularities (§4.4, §4.5), emits targeted templates for the common Cedar type-checker gotchas (§4.6), and self-validates its own planner output before Phase 2 begins (§5.4). Together these changes turned several previously-unsolvable scenarios into few-iteration convergences without any change to the underlying models.
