# Official Cedar Alignment Tracker

This note records the lightweight "Experiment C" evidence from
`docs/external_dataset_reuse_plan.md`: AutoCedar's generated artifacts should
stay aligned with the official Cedar language, CLI, examples, and symbolic
analysis surface.

## Source Background

Official Cedar source families:

- `cedar-policy/cedar`: Rust implementation, validator, CLI, and SymCC entry
  points.
- `cedar-policy/cedar-examples`: example Cedar applications and policy/schema
  material.
- `cedar-policy/cedar-spec`: Lean formalization and differential/randomized
  testing infrastructure for Cedar.

This tracker is not an NL-intent benchmark. It supports the formal-language
side of the paper: AutoCedar emits ordinary Cedar schemas and policy stores
that validate and can be checked with Cedar's symbolic-analysis commands.

## Local Toolchain

Checked on 2026-06-22:

```text
cedar-policy-cli 4.10.0
cedar symcc command available
```

The installed `cedar symcc --help` exposes the analysis commands AutoCedar uses
or compiles to:

```text
implies
always-denies
equivalent
disjoint
matches-implies
matches-disjoint
```

## Check-Type Mapping

| AutoCedar signal | Cedar/SymCC interpretation |
| --- | --- |
| `ceiling` | Candidate policy must imply the reviewed reference policy, so the candidate is no more permissive than the reviewed intent bound. |
| `floor` | Reviewed reference policy must imply the candidate, so the candidate permits at least the required positive slice. |
| `liveness` | Candidate must not always deny the relevant request space. |
| `disjointness` | Compiled into a ceiling-style check plus floor patching where necessary, using reviewed forbidden slices rather than treating the complement as an affirmative permission grant. |

## GitHub Official-Example-Derived Scenario

Local scenario:

```text
experiments/github/
```

This scenario models a GitHub-style repository permission system adapted from
official Cedar example material. It is useful because it exercises common Cedar
authorization patterns:

- entity-set membership,
- resource-to-parent traversal,
- principal/resource equality,
- boolean attributes such as `isArchived`,
- action groups,
- floor checks for required alternative authorization paths.

Local validation on 2026-06-22:

| Artifact/check | Result |
| --- | --- |
| `cedar validate --schema experiments/github/schema.cedarschema --policies experiments/github/candidate.cedar` | PASS |
| `cedar validate --schema experiments/github/schema.cedarschema --policies experiments/github/policy_store.cedar` | PASS |
| `cedar validate` for all `experiments/github/references/*.cedar` | PASS, 7 reference policies |
| `uv run python orchestrator.py --workspace experiments/github` | PASS, loss 0 |

Verifier plan result:

| Check | Result |
| --- | --- |
| `pull_safety` | PASS |
| `push_safety` | PASS |
| `edit_issue_safety` | PASS |
| `delete_issue_safety` | PASS |
| `add_reader_safety` | PASS |
| `writer_edit_floor` | PASS |
| `reporter_delete_floor` | PASS |
| `liveness_push` | PASS |
| `liveness_edit_issue` | PASS |

## Paper Interpretation

- Use this as **Cedar-language alignment evidence**, not as prose-intent
  extraction evidence. The REDE/ACRE tracker covers natural-language intent
  formalization; this tracker covers generated artifact compatibility with the
  official Cedar toolchain.
- The GitHub scenario shows that AutoCedar's floor/ceiling/liveness signals map
  cleanly onto Cedar validation and SymCC-style reasoning.
- The official Cedar examples are also the provenance root for AutoCedar's
  mutation benchmark families; the larger CedarBench/realworld counts should be
  reported separately from this small alignment smoke.

## Reproduce

```bash
cedar validate \
  --schema experiments/github/schema.cedarschema \
  --policies experiments/github/candidate.cedar \
  --error-format plain

cedar validate \
  --schema experiments/github/schema.cedarschema \
  --policies experiments/github/policy_store.cedar \
  --error-format plain

for p in experiments/github/references/*.cedar; do
  cedar validate \
    --schema experiments/github/schema.cedarschema \
    --policies "$p" \
    --error-format plain >/dev/null
done

CVC5="$(command -v cvc5)" uv run python orchestrator.py \
  --workspace experiments/github
```

The legacy orchestrator appends verified candidates to
`experiments/github/policy_store.cedar` as a side effect. If you use this only
as a smoke test, discard that append before committing unless the experiment is
intentionally updating the policy store.
