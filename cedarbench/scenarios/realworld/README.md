# CedarBench Realworld Scenarios

Hand-designed Cedar policy scenarios targeting production-use patterns
and specific verification-harness capabilities. Each scenario has a
natural-language `policy_spec.md`, a `schema.cedarschema`, a
`verification_plan.py` defining the checks the harness runs against a
synthesized candidate, and a `references/` directory of per-check
Cedar policy bounds.

This directory is companion to, and conceptually distinct from, the
auto-generated mutation scenarios in `cedarbench/scenarios/<domain>_*`.
The mutation scenarios are produced by a templated generator that
varies a base policy in structured ways; the realworld scenarios are
designed by hand to probe production patterns and harness edge cases.

## Scenario Index

| # | Scenario | Pattern | Difficulty | Novel Cedar feature / harness target |
|---|----------|---------|:----------:|--------------------------------------|
| 1 | [emergency_break_glass](./emergency_break_glass) | Emergency override with care-team baseline | medium | Narrow break-glass permit that unlocks only view, not edit |
| 2 | [approval_chain_workflow](./approval_chain_workflow) | Multi-signer approval state machine | medium | `set.containsAll()` for unanimous-consent gating |
| 3 | [multi_tenant_saas](./multi_tenant_saas) | Tenant isolation with global-support read path | medium | Narrow cross-tenant read with context attestation |
| 4 | [contextual_mfa_elevation](./contextual_mfa_elevation) | Step-up authentication | medium | `datetime.durationSince()` for MFA freshness |
| 5 | [legal_hold_override_expiry](./legal_hold_override_expiry) | Records management with conditional override | medium | Override interplay: legal hold extends edit past expiry |
| 6 | [delegation_temporary_grant](./delegation_temporary_grant) | Ephemeral grants via context attestation | medium | Optional context attribute with `has` guarding |
| 7 | [pii_data_classification](./pii_data_classification) | MLS / compartmentalization | medium | String-enum hierarchy + orthogonal forbid gates |
| 8 | [payroll_separation_of_duties](./payroll_separation_of_duties) | SOX Separation of Duties | medium | `principal != resource.initiator` + amount-threshold escalation |
| 9 | [api_key_scoped_access](./api_key_scoped_access) | Machine-to-machine authorization | medium | Non-User principal (`ApiKey`) + scope strings |
| 10 | [string_prefix_domain_match](./string_prefix_domain_match) | Email-pattern ACL | medium | Cedar's `like` glob operator (only string primitive) |
| 11 | [intentional_planner_contradiction](./intentional_planner_contradiction) | §8.8 regression test | hard (planning) | Self-referential corner case hunting unsatisfiable bounds |
| 12 | [hundred_check_scale](./hundred_check_scale) | Large-scale RBAC matrix | hard (scale) | 157-check stress test for conversation trimming and context |

## Pattern Taxonomy

The scenarios cover the following production-access-control patterns:

### Identity & authorization patterns
- **Care-team / ACL** — emergency_break_glass (1), legal_hold_override_expiry (5)
- **Ephemeral delegation** — delegation_temporary_grant (6)
- **Tenant isolation** — multi_tenant_saas (3)
- **Role-based access (RBAC)** — payroll_separation_of_duties (8), hundred_check_scale (12)
- **Multi-level security (MLS)** — pii_data_classification (7)
- **Machine-to-machine** — api_key_scoped_access (9)
- **Email / pattern-based ACL** — string_prefix_domain_match (10)

### Temporal & contextual patterns
- **Step-up authentication** — contextual_mfa_elevation (4)
- **Document expiry with hold override** — legal_hold_override_expiry (5)
- **Emergency time-windows** — emergency_break_glass (1)
- **Grant expiry** — delegation_temporary_grant (6)
- **API key expiry + revocation** — api_key_scoped_access (9)

### Workflow / state-machine patterns
- **Multi-signer approval** — approval_chain_workflow (2)
- **SOX Separation of Duties** — payroll_separation_of_duties (8)

### Meta / harness-stress patterns
- **§8.8 regression test** — intentional_planner_contradiction (11)
- **Scale stress** — hundred_check_scale (12)

## Cedar Features Exercised (First Appearance)

| Cedar feature | Scenario introducing it |
|---|---|
| `set.containsAll()` | approval_chain_workflow |
| `datetime.durationSince(other)` | contextual_mfa_elevation |
| `like` glob operator | string_prefix_domain_match |
| Non-User principal entity type | api_key_scoped_access |
| Narrow break-glass override permit | emergency_break_glass |
| Optional context attribute `?` with `has` guarding | delegation_temporary_grant |
| Record literal `set.contains({field: value, ...})` | (tax_base, CedarBench mutation) |

All other Cedar features exercised in this directory (entity hierarchies,
attribute access, `in` set membership, datetime comparisons, `unless`
clauses, forbid composition, record types as context attributes) are
also exercised by the CedarBench mutation scenarios and not repeated
in the above table.

## Metadata Format

Each `policy_spec.md` includes a YAML-style frontmatter block at the
top with the following fields:

- `pattern`: the named access-control pattern (see Pattern Taxonomy)
- `difficulty`: one of `easy`, `medium`, `hard`; semantic difficulty
  for the synthesizer (not scale)
- `features`: a bulleted list of Cedar features and structural
  properties exercised by the scenario
- `domain`: the real-world domain the scenario models (e.g.
  "healthcare", "finance / SOX compliance", "engineering / SRE")

Example:

```yaml
---
pattern: delegation (ephemeral grant)
difficulty: medium
features:
  - optional context attribute (`has` guarding)
  - datetime comparison on nested record attribute
  - fallback access path (owner vs grantee)
  - per-action scoping on the same grant
domain: engineering / SRE
---
```

## Running a Scenario

From the repo root:

```bash
python3 eval_harness.py \
  --scenario cedarbench/scenarios/realworld/<name> \
  --phase2-model claude-haiku-4-5-20251001 \
  --no-review --max-iters 20 \
  --run-id my_run
```

This uses the hand-authored `verification_plan.py` and `references/`
directly (no Phase 1 LLM call) and runs Phase 2 (synthesis) with the
specified Haiku version. Results land under
`eval_runs/<run-id>/<scenario_name>/`.

To regenerate Phase 1 with an LLM planner instead of the hand-authored
artifacts, add `--gen-references` and optionally
`--phase1-model claude-opus-4-6`.

## Current Results

All 12 scenarios converge under the post-fix harness (see
`docs/harness_fix_log.md` for the harness evolution):

| Scenario | Iterations | Checks | Cost |
|----------|:----------:|:------:|:----:|
| emergency_break_glass            | 1  | 7   | $0.003 |
| approval_chain_workflow          | 2  | 16  | $0.009 |
| multi_tenant_saas                | 3  | 10  | $0.011 |
| contextual_mfa_elevation         | 2  | 13  | $0.008 |
| legal_hold_override_expiry       | 1  | 11  | $0.003 |
| delegation_temporary_grant       | 2  | 12  | $0.008 |
| pii_data_classification          | 2  | 8   | $0.010 |
| payroll_separation_of_duties     | 1  | 15  | $0.004 |
| api_key_scoped_access            | 2  | 14  | $0.009 |
| string_prefix_domain_match       | 2  | 8   | $0.006 |
| intentional_planner_contradiction | 1  | 4   | $0.003 |
| hundred_check_scale              | 2  | 157 | $0.021 |
| **Total**                        | —  | **275** | **$0.095** |

Mean iterations to converge: **1.75**.
Mean cost per scenario: **$0.008**.

Phase 1 in every scenario is hand-authored (by the human / agent acting
as planner); Phase 2 is Haiku 4.5 via the Anthropic API. The cost
figures reflect Phase 2 Haiku tokens only; Phase 1 authoring cost is
zero in terms of API consumption.

## Citation

If you use these scenarios in academic work, please cite as:

```
CedarBench-Realworld: Hand-designed Cedar policy scenarios for
verification-harness evaluation. Part of the Cedar Synthesis Engine
repository. https://github.com/neselab/cedar-synthesis-engine
```
