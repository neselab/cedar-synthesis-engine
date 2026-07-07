# Ultra-Hard Corpus Scenario: iTrust Text2Policy-Derived Intent

This scenario is an iTrust case-study variant derived from Text2Policy-style
requirements material and formalized into Cedar.

It is included in CedarBench as an ultra-hard realworld scenario because it
tests a different source representation of the same healthcare authorization
domain: session-scoped access, credential restrictions, personal
representatives, patient-owned records, HCP duties, and administrator-only
operations.

## Files

- `source_intent.md` — curated source intent used for formalization.
- `policy_spec.md` — reviewed natural-language target summary.
- `schema.cedarschema` — reviewed Cedar schema.
- `verification_plan.py` — formal floor/ceiling/liveness/disjointness checks.
- `references/` — Cedar reference policies for the checks.
- `candidate.cedar` — converged policy artifact from the HITL run.
- `approved_property_atoms.json` — reviewed property decisions.

