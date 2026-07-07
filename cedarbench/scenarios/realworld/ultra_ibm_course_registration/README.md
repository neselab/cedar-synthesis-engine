# Ultra-Hard Corpus Scenario: IBM Course Registration

This scenario is a corpus-derived organizational access-control case study
based on the IBM course-registration requirements used in the REDE/NLACP-style
evaluation work.

It is included in CedarBench as an ultra-hard realworld scenario because the
target is not a single local rule. The policy must compose student ownership,
registration lifecycle state, professor assignment, professor eligibility,
schedule conflicts, grade sensitivity, and registrar-only operations.

## Files

- `policy_spec.md` — reviewed natural-language intent summary.
- `schema.cedarschema` — reviewed Cedar schema.
- `verification_plan.py` — formal floor/ceiling/liveness checks.
- `references/` — Cedar reference policies for the checks.
- `candidate.cedar` — converged policy artifact from the manual AITL run.
- `approved_property_atoms.json` / `.md` — reviewed property atoms.
- `TRACE.md` — source/run notes from the manual AITL construction.

