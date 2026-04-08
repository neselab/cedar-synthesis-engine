# CedarBench

A large-scale benchmark dataset for evaluating automated Cedar policy
synthesis and verification. CedarBench consists of two complementary
sets of scenarios:

1. **Mutation scenarios** (`scenarios/<domain>_*`) — 79 auto-generated
   scenarios produced by systematically mutating eight base policies
   drawn from the [cedar-examples][cedar-examples] repository. Each
   mutation exercises a specific kind of policy change (add a role,
   remove a constraint, add a new action, etc.), testing whether a
   policy synthesizer can keep up with realistic evolution of a
   specification.
2. **Realworld scenarios** (`scenarios/realworld/*`) — 12 hand-designed
   scenarios targeting specific production access-control patterns and
   Cedar features. Each realworld scenario is authored to probe a
   particular real-world workflow (emergency break-glass, approval
   chains, multi-tenant SaaS, MFA elevation, etc.) with enough
   fidelity that the result is suitable for both harness evaluation
   and as a reference implementation for practitioners.

Together, CedarBench provides **91 verification-ready scenarios**,
each with a natural-language specification, a Cedar schema, and a
hand- or auto-authored verification plan defining the checks the
harness runs against a synthesized candidate policy.

To our knowledge this is the first large-scale dataset of Cedar
policies with both natural-language specifications and formal
verification plans, suitable for benchmarking LLM-based policy
synthesis, formal verification, and CEGIS-style feedback loops.

## Structure

```
cedarbench/
├── README.md                 # this file
├── scenarios/                # 91 total scenarios
│   ├── <domain>_base/        # 8 domain-base scenarios
│   ├── <domain>_add_X/       # domain × mutation scenarios
│   ├── <domain>_remove_X/    # (79 total mutation scenarios)
│   ├── <domain>_full_expansion/
│   └── realworld/            # 12 hand-designed scenarios
│       ├── README.md         # realworld-specific index
│       └── <scenario>/
├── base_scenarios.py         # definitions for the 8 base scenarios
├── generate.py               # mutation generator
├── mutation.py               # mutation operator definitions
├── mutations/                # mutation templates
└── schema_ops.py             # schema-mutation helpers
```

Each scenario directory contains:

```
<scenario_name>/
├── policy_spec.md            # natural-language requirements
├── schema.cedarschema        # Cedar schema (entities, actions, context)
├── verification_plan.py      # check definitions (named get_checks())
└── references/               # per-check Cedar bounds
    └── *.cedar               # one file per ceiling or floor reference
```

## The Eight Domains (Mutation Scenarios)

| Domain    | Count | Source                                         | Description |
|-----------|:-----:|------------------------------------------------|-------------|
| github    | 14    | [cedar-examples/github_example][gh]            | Repository permissions with archive blocking |
| clinical  | 11    | cedar-synthesis-engine own corpus              | Clinical-trial data platform with roles & clearance |
| doccloud  | 10    | [cedar-examples/document_cloud][doc]           | Cloud document sharing with ACLs and blocking |
| streaming | 10    | [cedar-examples/streaming_service][stream]     | Streaming service with subscription tiers & datetime rules |
| tax       | 8     | [cedar-examples/tax_preparer][tax]             | Tax-preparer org-matching with consent forbid |
| tags      | 8     | [cedar-examples/tags_n_roles][tags]            | Role-scoped tag namespaces with wildcard matching |
| sales     | 9     | [cedar-examples/sales_orgs][sales]             | Sales organization with job-based segmentation |
| hotel     | 9     | [cedar-examples/hotel_chains][hotel]           | Hotel chain hierarchy with viewer/member/admin roles |
| **Total** | **79** |                                              |             |

Each base scenario is further mutated by the mutation generator
(`generate.py` + `mutations/`) into 8–14 scenario variants that add,
remove, or modify a single aspect of the base policy.

## The Twelve Realworld Scenarios

See `scenarios/realworld/README.md` for the full index. A summary:

| # | Scenario | Pattern |
|---|----------|---------|
| 1 | emergency_break_glass | Healthcare break-glass with care-team baseline |
| 2 | approval_chain_workflow | Multi-signer approval state machine |
| 3 | multi_tenant_saas | Tenant isolation with global-support read |
| 4 | contextual_mfa_elevation | Step-up authentication with MFA freshness |
| 5 | legal_hold_override_expiry | Records management with legal hold |
| 6 | delegation_temporary_grant | Ephemeral grants via context attestation |
| 7 | pii_data_classification | MLS / clearance / need-to-know |
| 8 | payroll_separation_of_duties | SOX Separation of Duties |
| 9 | api_key_scoped_access | Machine-to-machine with scope strings |
| 10 | string_prefix_domain_match | Email-based ACL using Cedar's `like` |
| 11 | intentional_planner_contradiction | Self-referential corner case |
| 12 | hundred_check_scale | 157-check scale stress test |

## Running a Scenario

```bash
# From the repository root
python3 eval_harness.py \
    --scenario cedarbench/scenarios/<scenario_name> \
    --phase2-model claude-haiku-4-5-20251001 \
    --no-review --max-iters 20 \
    --run-id my_run

# Run all 91 scenarios in sequence
python3 eval_harness.py \
    --all \
    --phase2-model claude-haiku-4-5-20251001 \
    --no-review --max-iters 20 \
    --run-id full_benchmark
```

Each scenario produces:
- `eval_runs/<run_id>/<scenario>/candidate.cedar` — the final
  synthesized Cedar policy
- `eval_runs/<run_id>/<scenario>/eval_log.json` — per-iteration loss,
  check results, token counts, and timing
- `eval_runs/<run_id>/summary.json` — aggregate results

The harness runs a two-phase CEGIS loop: Phase 1 (planner) reads the
spec and schema to emit the verification plan and reference policies;
Phase 2 (synthesizer) iteratively proposes candidate Cedar policies
and corrects them based on symbolic-verifier feedback. For details on
the harness evolution and signal-layer fixes, see
`../docs/harness_fix_log.md`.

## Evaluation Protocol

A typical benchmark run records, per scenario:
- **Converged** (yes/no) — did the synthesizer produce a policy that
  passes all verification checks within the iteration budget?
- **Iterations to converge** — how many CEGIS iterations were
  required; lower is better
- **Total checks** — the number of property checks in the verification
  plan; not a difficulty indicator on its own
- **Tokens / cost** — how many input and output tokens the Phase 2
  synthesizer consumed, and the resulting API cost

Under the current post-fix harness (as of the latest commit on
`main`), all 91 scenarios converge successfully with Haiku 4.5 as
the Phase 2 synthesizer.

## Citation

If you use CedarBench in academic work, please cite:

```
CedarBench: A verification-ready dataset of Cedar access-control
policies for LLM synthesis evaluation. Part of the Cedar Synthesis
Engine repository, available at
https://github.com/neselab/cedar-synthesis-engine
```

## License

The benchmark scenarios are released under the same license as the
parent Cedar Synthesis Engine repository. The upstream cedar-examples
corpus is licensed separately; see the upstream repository for details.

[cedar-examples]: https://github.com/cedar-policy/cedar-examples
[gh]: https://github.com/cedar-policy/cedar-examples/tree/main/cedar-example-use-cases/github_example
[doc]: https://github.com/cedar-policy/cedar-examples/tree/main/cedar-example-use-cases/document_cloud
[stream]: https://github.com/cedar-policy/cedar-examples/tree/main/cedar-example-use-cases/streaming_service
[tax]: https://github.com/cedar-policy/cedar-examples/tree/main/cedar-example-use-cases/tax_preparer
[tags]: https://github.com/cedar-policy/cedar-examples/tree/main/cedar-example-use-cases/tags_n_roles
[sales]: https://github.com/cedar-policy/cedar-examples/tree/main/cedar-example-use-cases/sales_orgs
[hotel]: https://github.com/cedar-policy/cedar-examples/tree/main/cedar-example-use-cases/hotel_chains
