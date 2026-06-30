---
pattern: ambiguous spec / most-restrictive interpretation
difficulty: hard (planning)
features:
  - explicit-grant gating
  - role-bounded permits
  - hedged natural-language requirements
domain: governance / least-privilege defaults
synthesis_difficulty: 4
---

# Ambiguous Specification — Policy Specification

## Context

This policy governs `view` and `approve` actions on `Document` entities
by `User` principals. The natural-language spec below is INTENTIONALLY
hedged: words like "typically", "may sometimes", and "high-impact" are
deliberately vague.

The convention this scenario codifies is the **least-privilege default**:

> **When the specification is ambiguous, the planner MUST choose the
> MOST RESTRICTIVE interpretation that is consistent with the text.**

In other words, when the spec says "admins typically have access," the
correct planner reading is "permit admins ONLY when explicitly granted,"
not "permit admins by default and carve out exceptions." Hedged language
("typically", "sometimes", "may") is read as "only when explicitly
authorized" — never as "by default."

## Requirements (deliberately hedged)

### 1. Viewing Documents
- "Admins typically have access to most resources, except under special
  circumstances."
- "Regular users may sometimes view sensitive documents."

### 2. Approving Documents
- "Approval is required for high-impact actions, and only certain
  privileged users can perform approvals."
- "Approvals are not routine — they happen under controlled conditions."

## Restrictive Interpretation (what the planner MUST encode)

Reading the above with the most-restrictive lens:

### View
- A `User` may `view` a `Document` ONLY IF:
  - `principal.explicitGrant == true`, AND
  - `principal.role == "admin"` OR `principal.role == "user"`.
- "Typically" and "may sometimes" are read as "requires explicit grant."
- Any other role (e.g. `"guest"`) is denied even with a grant.

### Approve
- A `User` may `approve` a `Document` ONLY IF:
  - `principal.explicitGrant == true`, AND
  - `principal.role == "admin"`.
- "Only certain privileged users" is read as "admins only" (the strictest
  reading consistent with the spec).
- "Not routine" reinforces the explicit-grant requirement.

## Floors (what MUST be permitted under the restrictive reading)

Even under the strictest reading, the spec implies SOME positive cases:

- An admin with an explicit grant MUST be able to `view` any document.
  (Otherwise "admins typically have access" would be vacuous.)
- A regular user with an explicit grant MUST be able to `view` any
  document. (Otherwise "users may sometimes view" would be vacuous.)
- An admin with an explicit grant MUST be able to `approve` any document.
  (Otherwise "certain privileged users can perform approvals" would be
  vacuous.)

These floors are the MINIMUM positive cases required to make the spec
non-trivial. Anything beyond them (e.g. "admin without grant can view")
is forbidden by the most-restrictive reading.

## Notes

- This scenario tests whether the synthesizer (Haiku, in Phase 2) reads
  hedged natural language with the same least-privilege bias the planner
  used. Both must converge on the same restrictive interpretation for
  the candidate to satisfy the references.
- The convention "ambiguous → most-restrictive" is widely advocated in
  security engineering (cf. principle of least privilege, deny-by-default).
- The schema fields `explicitGrant: Bool` and `requiresApproval: Bool`
  are what allow the restrictive reading to be expressed precisely. A
  permissive reading would ignore `explicitGrant` and only check role.
