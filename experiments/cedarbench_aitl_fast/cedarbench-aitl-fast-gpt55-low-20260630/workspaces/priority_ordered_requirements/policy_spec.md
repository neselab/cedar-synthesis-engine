---
pattern: priority-ordered conflicting requirements
difficulty: hard
features:
  - explicit rule priority chain
  - conflicting rule resolution via guards
  - negation of higher-priority conditions on lower-priority rules
domain: data governance / compliance
synthesis_difficulty: 4
---

# Priority-Ordered Requirements — Policy Specification

## Context

This policy implements **explicit priority ordering between conflicting
access rules** for a record store. Three independent rules can each
authorize access to a record, but they may overlap. When two or more
rules apply simultaneously, the rule with the highest priority wins —
lower-priority rules MUST NOT grant access in scenarios already covered
(or excluded) by a higher-priority rule.

The encoding challenge: lower-priority rules must explicitly negate the
trigger conditions of every higher-priority rule, so that the combined
permit clause behaves as a strict precedence chain rather than an
unstructured disjunction.

## Entities

- **User** — `role: String` — values include `"legal_team"`, `"reader"`,
  and other organizational roles. `pii_clearance: Bool` — whether the
  user holds active PII clearance.
- **Record** — `legalHold: Bool` — true when the record is under legal
  hold. `containsPII: Bool` — true when the record contains personally
  identifiable information.

## Action

- **access** — read access to a `Record` by a `User`.

## Access rules (PRIORITY ORDER)

Three rules apply, with the following priority chain:

### R1 — HIGHEST: Legal hold

If `resource.legalHold == true`, access is permitted **only** to users
whose `role == "legal_team"`. Nothing else applies — even a user with
`pii_clearance` cannot bypass legal hold, and a user with the
`"reader"` role cannot fall back to R3. Legal hold strictly narrows the
permitted population.

### R2 — MEDIUM: PII clearance

If `resource.containsPII == true` AND legal hold does not apply, access
is permitted **only** to users with `pii_clearance == true`. The
`"reader"` role does NOT grant access to PII records on its own —
clearance is required.

### R3 — LOWEST: Default reader access

If neither legal hold nor PII applies (i.e., `legalHold == false` AND
`containsPII == false`), then any user with `role == "reader"` may
access the record.

## Conflict-resolution semantics

When R1 and R2 both apply (`legalHold == true` AND `containsPII == true`),
**R1 wins**: only `legal_team` may access, regardless of `pii_clearance`.
A user with `pii_clearance` who is NOT on the legal team is denied.

When R2 and R3 both apply (`containsPII == true` AND user has the
`"reader"` role), **R2 wins**: a reader without `pii_clearance` is
denied; only readers (or any user) with `pii_clearance` may access.

R1 and R3 cannot both nominally apply at the same time without R2 also
applying, but the same precedence holds: R1 strictly narrows.

## Notes

- The encoding pattern is: lower-priority rules carry explicit
  negations of every higher-priority rule's trigger condition in their
  `when` guard. A naive disjunction (`R1_perm || R2_perm || R3_perm`)
  is too permissive because it lets a `reader` access a PII record
  (R3 firing while R2's gate is also true) or lets a cleared user
  access a legal-hold record (R2 firing while R1's gate is also true).
- Common failure modes: (a) omitting the `!resource.legalHold` guard
  on R2 or R3 — letting non-legal-team users access legal-hold
  records; (b) omitting the `!resource.containsPII` guard on R3 —
  letting unCLEARED readers access PII records; (c) dropping role
  checks under the misconception that priority alone is sufficient.
