---
pattern: decoy trivial properties
difficulty: medium
features:
  - role-based-access
  - attribute-comparison
  - trivially-true-floors
  - verification-plan-stress
domain: harness-meta
synthesis_difficulty: 3
---

# Decoy Trivial Properties — Policy Specification

## Context

This scenario stress-tests the verification harness with a plan that
deliberately mixes a small number of *substantive* checks (one ceiling and
three floors that bound the actual policy rule) with a larger set of
*trivially true* floors (`permit when true`-style references).

The trivial floors are vacuously satisfied by any sound candidate that
permits at least one request. They exist to verify that:

1. The harness correctly counts trivial floors as PASSed without burning
   iterations on them.
2. A reasonable candidate produced by Phase 2 converges quickly even when
   the verification plan is padded with low-information checks.

This file is a "decoy" plan in the sense that most of its checks carry no
real signal — only the three hard floors and one ceiling actually pin the
candidate down.

## Entities

- `User` with attribute `role: String` — the role this user holds.
  Expected values are `"admin"` and `"user"` (other strings are denied).
- `Resource` with attribute `level: Long` — a non-negative sensitivity
  level.

## Action

- `access` — applies to a `User` principal and a `Resource` resource. No
  context is required.

## Authorization Rule

A principal is permitted to `access` a resource if and only if:

```
principal.role == "admin"
|| (principal.role == "user" && resource.level <= 3)
```

In words:

- **Admins** may access any resource regardless of `level`.
- **Users** (`role == "user"`) may access a resource only when
  `resource.level <= 3`.
- All other principals (any other `role` string) are denied.

## Hard Properties

The plan encodes one ceiling and three substantive floors that fully
constrain the rule above:

1. **Ceiling (`access_ceiling`)**: any permit must satisfy
   `principal.role == "admin" || (principal.role == "user" && resource.level <= 3)`.
2. **Floor (`admin_any_level_must_permit`)**: an `admin` accessing a
   resource at any `level` must be permitted.
3. **Floor (`user_low_level_must_permit`)**: a `user` accessing a resource
   with `level <= 3` must be permitted.
4. **Floor (`user_zero_level_must_permit`)**: a `user` accessing a
   resource with `level == 0` must be permitted (a strict subset of #3 —
   still hard, since it pins the rule on a specific value).

## Trivially-True Floors (Decoy)

The plan also contains five floors whose reference body is a tautological
`permit when <true expression>`. Any candidate that permits at least one
request in the action's slice satisfies these vacuously:

- `trivial_floor_true` — `permit when true`
- `trivial_floor_one_eq_one` — `permit when 1 == 1`
- `trivial_floor_string_eq` — `permit when "x" == "x"`
- `trivial_floor_or_true` — `permit when (1 == 2) || true`
- `trivial_floor_not_false` — `permit when !(1 == 2)`

These checks are designed to PASS with no iteration cost.

## Liveness

- `liveness_access` — at least one `User` × `access` × `Resource`
  request must be permitted by the candidate.

## Notes

- Cedar denies by default, so the substantive ceiling is what bounds
  over-permissive candidates.
- The trivial floors test the harness's counting and reporting, not the
  candidate's correctness. They should always show PASS.
- A correctly-converged candidate is essentially a single `permit` whose
  body matches the rule above.
