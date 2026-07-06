# Cedar Policy Synthesis: Course Registration

This is a draft Terminal-Bench Science task for the Engineering Sciences / Autoformalization lane.

The task asks a terminal agent to synthesize a deployable Cedar policy store from realistic natural-language course-registration access-control requirements. The agent receives a requirements document and a Cedar schema, then writes `/app/policy.cedar`.

## Why This Task Matters

Access-control policy authoring is a practical formalization workflow: informal organizational requirements must become executable policy code without over-permitting sensitive workflows. This task tests whether agents can use a terminal, inspect a schema, write Cedar, run validation, and repair policy code until it satisfies hidden semantic boundaries.

## Files

- `instruction.md` — instructions shown to the agent.
- `requirements.md` — natural-language access-control requirements.
- `schema.cedarschema` — provided application authorization schema.
- `policy.cedar` — empty starter file the agent must replace.
- `solution/solve.sh` — oracle solution for sanity checking.
- `tests/test_policy_semantics.py` — hidden verifier using Cedar validation and SymCC.
- `tests/test.sh` — Harbor verifier entry point.

## Verification

The verifier checks:

1. Cedar syntax/type correctness with `cedar validate`.
2. Ceiling properties with `cedar symcc implies`.
3. Floor properties with `cedar symcc implies` in the opposite direction.
4. Liveness by rejecting policies that always deny key request classes.

The verifier accepts any policy that satisfies the semantic target, not only the oracle solution.

## Local Sanity Check

With Cedar CLI 4.10.0 and CVC5 installed:

```bash
APP_DIR="$PWD" ./solution/solve.sh
APP_DIR="$PWD" python3 tests/test_policy_semantics.py
```

A deliberately broad policy such as `permit (principal, action, resource);` fails the hidden ceiling checks.
