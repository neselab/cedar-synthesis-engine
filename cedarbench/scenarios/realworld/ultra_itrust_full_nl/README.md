# Ultra-Hard Corpus Scenario: iTrust Full Natural-Language Intent

This scenario is the full iTrust natural-language access-control case study
formalized into a reviewed Cedar schema, property target, and policy store.

It is included in CedarBench as an ultra-hard realworld scenario because it
contains many interacting healthcare authorization workflows: patient and
representative self-access, HCP/LHCP/UAP duties, diagnostic-information
restriction, deactivated-patient restrictions, administrator duties, public
health reports, lab technician queues, emergency reports, access logs, and
patient messaging.

## Files

- `source_intent.md` — source natural-language intent document.
- `policy_spec.md` — generated Stage 3 target summary from reviewed atoms.
- `schema.cedarschema` — reviewed Cedar schema.
- `verification_plan.py` — formal floor/ceiling/liveness/disjointness checks.
- `references/` — Cedar reference policies for the checks.
- `candidate.cedar` — converged policy artifact from the final run.
- `approved_property_atoms.json` — reviewed property atoms.

Note: `candidate.cedar` is preserved as the final run artifact. It passes Cedar
validation, but Cedar reports warnings for a few impossible/no-op rules. The
benchmark target itself is defined by `verification_plan.py` and `references/`,
and all reference policies validate cleanly against the schema.
