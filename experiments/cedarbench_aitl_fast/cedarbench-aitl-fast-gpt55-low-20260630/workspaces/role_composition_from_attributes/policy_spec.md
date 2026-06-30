---
pattern: effective-role computed inline from attribute combination — no explicit role attribute
difficulty: medium
features:
  - role inferred from attribute conjunction (no `principal.role` field exists)
  - set-membership check (`certifications.contains("MGMT-101")`)
  - multi-attribute conjunction as a manager predicate
  - employment-status gating
  - schema deliberately omits a `role` attribute
domain: workforce identity / RBAC-from-ABAC composition
synthesis_difficulty: 3
---

# Role Composition From Attributes — Policy Specification

## Context

This policy implements **role composition from attributes**: the
"manager" role is NOT stored as a `role` attribute on `Employee`.
Instead, it is **computed inline** from a conjunction of three
employee attributes — `seniority`, `certifications`, and
`employmentStatus`. A principal is an "effective manager" iff all
three predicates simultaneously hold.

Principal is `Employee`; resource is `Resource`. Two actions are
defined: `view` (any active employee) and `manage` (effective
manager only).

## Schema notes

- `Employee` has exactly three attributes: `seniority: Long`,
  `certifications: Set<String>`, and `employmentStatus: String`.
- The schema **deliberately omits** a `role` attribute. The
  synthesizer must NOT introduce a `principal.role` reference —
  doing so will fail schema validation.

## Requirements

### 1. View Access (Permit)

- Any `Employee` whose `employmentStatus == "active"` may perform
  `view` on any `Resource`.
- Inactive employees (any `employmentStatus` other than `"active"`,
  e.g. `"terminated"`, `"on_leave"`, `"suspended"`) MUST NOT view.

### 2. Manage Access (Permit)

An `Employee` may perform `manage` on a `Resource` if AND ONLY IF
ALL of the following predicates hold simultaneously (the effective
"manager" condition):

  - `principal.employmentStatus == "active"`,
  - `principal.seniority >= 5`,
  - `principal.certifications.contains("MGMT-101")`.

These three predicates together constitute the effective manager
role. There is NO short-circuit via a stored `role` attribute.

### 3. Default Deny

- An employee missing any one of the three manager predicates
  (e.g. seniority 4, no MGMT-101, or not active) MUST be denied
  `manage`.
- An inactive employee MUST be denied both `view` and `manage`
  regardless of seniority or certifications held.

## Notes

- There is **no `principal.role` attribute**. Common failure mode:
  the synthesizer imagines a `role` attribute and writes
  `principal.role == "manager"`. This will fail schema validation
  because the schema declares only `seniority`, `certifications`,
  and `employmentStatus`.
- The check `principal.certifications.contains("MGMT-101")` uses
  Cedar's `Set::contains` method — `certifications` is `Set<String>`.
- All three conjuncts for `manage` are independent — none may be
  dropped or weakened.
