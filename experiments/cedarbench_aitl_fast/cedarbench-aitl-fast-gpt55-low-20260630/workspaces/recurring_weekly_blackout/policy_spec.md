---
pattern: recurring weekly blackout via host attestation
difficulty: medium
features:
  - host-supplied boolean attestation
  - optional context attribute (datetime)
  - role-based override (oncall)
  - inverted gating (emergency only during blackout)
domain: SRE / change management
synthesis_difficulty: 3
---

# Recurring Weekly Blackout -- Policy Specification

## Context

Many production systems have recurring weekly blackout windows during
which routine changes are prohibited (for example, every Sunday from
02:00-04:00 UTC for backup processing, or every Friday afternoon as a
"no deploy" window). Cedar has no modulo or weekday/time-of-day
arithmetic operators, so the host application is responsible for
computing whether the current moment falls inside a blackout window
and passing the answer to Cedar as a boolean attestation.

This pattern -- "host attestation" -- is the standard Cedar workaround
for any predicate the policy language cannot itself compute. The host
is trusted to compute `inBlackoutWindow` correctly; the policy is
responsible for routing the right principals to the right actions
based on that boolean.

Entities: `User` (with `role: String`) and `System`. The role is
either `"user"` (ordinary engineer) or `"oncall"` (on-call SRE).

The context for both actions carries:
- `now: datetime` -- the current time, used for audit/logging only.
- `inBlackoutWindow: Bool` -- the host's attestation of whether the
  current time is inside a recurring blackout window.
- `blackoutEnds: datetime` (OPTIONAL) -- if currently in a blackout,
  when the blackout is scheduled to end. Absent when not in a
  blackout, and may also be absent during a blackout if the host
  cannot determine the end time.

Two actions: `access` (routine system access) and `emergencyAccess`
(emergency on-call access during a blackout).

## Requirements

### 1. Routine Access Outside Blackout (Permit)
- A User with role `"user"` may perform the `access` action on a
  System resource ONLY when `context.inBlackoutWindow` is `false`.
- A User with role `"oncall"` may perform the `access` action on a
  System resource at any time, regardless of `context.inBlackoutWindow`.
  On-call engineers are trusted to perform routine work even during a
  blackout; the blackout is a guideline for them, not a hard barrier.

### 2. Emergency Access -- Oncall Only, Blackout Only (Permit)
- A User with role `"oncall"` may perform the `emergencyAccess` action
  on a System resource ONLY when `context.inBlackoutWindow` is `true`.
  The emergency action is intentionally scoped to blackout windows
  because that is when ordinary access is restricted; outside a
  blackout the on-call engineer should use the routine `access` path.
- Users with any other role may NEVER perform `emergencyAccess`.
- `emergencyAccess` is forbidden when `context.inBlackoutWindow` is
  `false`, regardless of role.

## Notes

- `inBlackoutWindow` is computed by the host application. Cedar has
  no modulo operator and no weekday/hour-of-day function, so the
  host is the only place the recurring schedule can be evaluated.
- `blackoutEnds` is an optional attribute. Per harness rule §8.3,
  any policy that reads it must `has`-guard the read first. The
  reference policies in this scenario do not read `blackoutEnds`;
  it is declared as part of the realistic schema for downstream
  audit logging.
- Cedar denies by default. The absence of a permit for `user` role
  during a blackout (for `access`) and for any non-oncall principal
  (for `emergencyAccess`) is sufficient to enforce those rules.
- The role values are exactly `"user"` and `"oncall"`. No other
  roles exist in this system.
