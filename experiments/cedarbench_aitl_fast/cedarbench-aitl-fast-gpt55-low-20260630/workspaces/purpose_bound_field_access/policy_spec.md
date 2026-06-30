---
pattern: purpose-bound field access (data minimization)
difficulty: hard
features:
  - purpose-of-use binding
  - field-level access control
  - per-purpose set membership
  - explicit branching (no dynamic record key access)
domain: healthcare / data minimization
synthesis_difficulty: 4
---

# Purpose-Bound Field Access -- Policy Specification

## Context

This policy enforces **purpose-of-use** data minimization on patient
records. Each access carries a *declared purpose* (treatment, billing,
or research) and a *requested field name*. The policy must enforce two
things simultaneously:

1. The requesting workforce member's role matches the declared purpose
   (clinicians can only declare "treatment", billing clerks only
   "billing", researchers only "research").
2. The requested field is in the resource's per-purpose allowlist for
   that declared purpose.

The "right" mental model is a record keyed by purpose:
`resource.purposeFields[declaredPurpose].contains(requestedField)`. **This
is exactly what Cedar does NOT support.** Cedar has no dynamic record
key access -- record fields are accessed only by literal name. The
correct encoding maintains three separate `Set<String>` attributes on
the resource (one per purpose) and uses an explicit OR-branching
permit policy that selects the right set based on the declared purpose
literal.

## Entities

- `Workforce` with `role: String` -- one of `"clinician"`,
  `"billing_clerk"`, `"researcher"`. Other roles are unsupported.
- `PatientRecord` with three field allowlists:
  - `purposeFieldsTreatment: Set<String>` -- fields visible for treatment
  - `purposeFieldsBilling: Set<String>` -- fields visible for billing
  - `purposeFieldsResearch: Set<String>` -- fields visible for research

## Action

- `accessField` with context:
  - `requestedField: String`
  - `declaredPurpose: String` -- one of `"treatment"`, `"billing"`,
    `"research"`. Any other value MUST be denied.

## Requirements

### 1. Purpose-Bound Field Access (Permit)

A `Workforce` member may perform `accessField` on a `PatientRecord`
ONLY IF one of the following three branches holds:

- `context.declaredPurpose == "treatment"` AND
  `principal.role == "clinician"` AND
  `resource.purposeFieldsTreatment.contains(context.requestedField)`, OR
- `context.declaredPurpose == "billing"` AND
  `principal.role == "billing_clerk"` AND
  `resource.purposeFieldsBilling.contains(context.requestedField)`, OR
- `context.declaredPurpose == "research"` AND
  `principal.role == "researcher"` AND
  `resource.purposeFieldsResearch.contains(context.requestedField)`.

Any request whose declaredPurpose is not one of the three supported
literals MUST be denied. Any request whose role does not match the
purpose MUST be denied. Any request for a field not in the matching
purpose-allowlist MUST be denied.

### 2. Cross-Purpose Field Leakage (Forbid by Omission)

A clinician requesting a billing-only field (e.g. a field present in
`purposeFieldsBilling` but absent from `purposeFieldsTreatment`) MUST
be denied -- even if they declare purpose "treatment". The fields are
purpose-scoped, not role-scoped.

### 3. Floors

- A clinician declaring purpose "treatment" requesting a field that
  IS in `purposeFieldsTreatment` MUST be permitted.
- A billing clerk declaring purpose "billing" requesting a field that
  IS in `purposeFieldsBilling` MUST be permitted.
- A researcher declaring purpose "research" requesting a field that
  IS in `purposeFieldsResearch` MUST be permitted.

## Notes

- Cedar denies by default; no explicit forbid is required for the
  cross-purpose / wrong-role / unsupported-purpose cases.
- The LLM trap: the natural object-oriented encoding is
  `resource.purposeFields[context.declaredPurpose].contains(...)`.
  Cedar has no record subscript operator. The candidate MUST enumerate
  the three purposes explicitly with OR-branching and select the
  matching `Set<String>` attribute by literal field access.
- The role-purpose pairing is intentional: even if a clinician knew
  the shape of a billing record, declaring "billing" wouldn't help
  because their role is not `"billing_clerk"`.
