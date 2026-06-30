---
pattern: implicit deny-by-default
difficulty: medium
features:
  - role-based access (nurse, doctor, administrator)
  - implicit deny-by-default (allowed actions only listed)
  - role-intersection trap (multi-role principals)
  - positive-permit-only encoding
domain: healthcare
synthesis_difficulty: 2
---

# Implicit Deny-by-Default — Patient Chart Access

## Context

This policy governs access to patient `Chart` records in a hospital
information system. Three workforce roles interact with charts:
**nurses**, **doctors**, and **administrators**. Each `Worker` carries
a `role: String` attribute. There are three actions on a `Chart`:
`view`, `edit`, and `archive`.

The spec below lists ONLY the allowed combinations of (role, action).
Any (role, action) combination not explicitly listed is denied. This
follows Cedar's standard semantics: in the absence of a matching permit,
access is denied.

## Requirements

The following matrix lists every permitted (role, action) combination:

- A **nurse** can `view` patient charts.
- A **doctor** can `view` and `edit` patient charts.
- An **administrator** can `view`, `edit`, and `archive` patient charts.

## Notes

- Cedar denies by default, so the absence of a matching permit is
  sufficient to block unauthorized access. The spec deliberately does
  NOT enumerate negative cases (e.g. "nurses cannot edit charts") —
  the convention is that anything not on the allowed list is denied.
- Encode access as positive permits only. Do NOT add `forbid when
  principal.role == "X"` rules: a `Worker` may carry only one role
  here, but the role-intersection trap (§8.6) is real for any
  membership-style attribute. A negative-keyed forbid is fragile and
  needlessly couples permits across actions.
- The role values `"nurse"`, `"doctor"`, `"administrator"` are
  exhaustive for this spec. Any other role string yields denial for
  all three actions.
- There are no contextual conditions (no time-of-day, no consent
  attribute, no patient relationship): the access decision is purely
  a function of the principal's `role` and the action.
