# Cedar Policy Synthesis — Agent Instructions

You are an autonomous agent synthesizing a formally verified Cedar policy.

## Phase 1: Verification Plan (Agent A — One-Time Setup)

> Skip if `workspace/verification_plan.py` and `workspace/references/` already exist.

1. **Read** `workspace/policy_spec.md` (NL rules) and `workspace/schema.cedarschema`
2. **Generate** a verification plan → `workspace/verification_plan.py`
   - For each safety rule: create an `implies` check with a ceiling reference policy in `workspace/references/`
   - For each liveness rule: create an `always-denies-liveness` check
   - Add `never-errors` checks for each action
3. **Stop** for human review of the verification plan and reference policies.

## Phase 2: Policy Synthesis Loop (Agent B)

1. Initialize `results.tsv`: `iteration\tloss\tstatus\tdescription`

### Loop (until loss == 0 or 20 iterations)

1. **Write** `workspace/candidate.cedar`
2. **Run**: from the repository root, use `CVC5=~/.local/bin/cvc5 uv run python orchestrator.py`.
3. **Read** output:
   - `✓ PASS` / `✗ FAIL` per check
   - `loss: N` — number of failed checks
   - Counterexamples for failed `implies` checks
4. **Log** to `results.tsv`
5. **If loss > 0**: fix based on counterexamples, loop
6. **If loss == 0**: done, policy is verified

### Rules
- Only edit `workspace/candidate.cedar` and `results.tsv`
- Do NOT modify schema, references, verification plan, orchestrator, or solver_wrapper

### Cedar Cheatsheet
```cedar
permit (principal, action == Action::"delete", resource)
when { principal.department == "Engineering" && !resource.is_locked };
```

## Workspace Layout
```
workspace/
├── schema.cedarschema       # Cedar schema (READ-ONLY)
├── policy_spec.md            # NL rules (READ-ONLY)
├── policy_store.cedar        # Existing policies (READ-ONLY)
├── verification_plan.py      # List of checks — Agent A generates
├── references/               # Ceiling policies — Agent A generates
│   └── ceiling_delete.cedar
└── candidate.cedar           # YOUR OUTPUT
```
