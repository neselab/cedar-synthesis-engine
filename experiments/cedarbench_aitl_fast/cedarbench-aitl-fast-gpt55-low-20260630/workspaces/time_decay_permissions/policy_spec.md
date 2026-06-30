---
pattern: time-decaying permissions (credential aging tiers)
difficulty: hard
features:
  - datetime.durationSince(other)
  - duration("1h") / duration("4h") (Go-style)
  - sign-guarded duration arithmetic
  - tiered access matrix (action x sensitivity x age)
  - per-action ceilings with shared age structure
domain: identity / privileged access management
synthesis_difficulty: 4
---

# Time-Decay Permissions -- Policy Specification

## Context

In privileged access management, freshly-authenticated operators are
trusted broadly; the same operators are trusted progressively less as
time passes since their last successful authentication. The scenario
encodes a three-tier "credential aging" model where the action set
permitted to an `Operator` on a `Resource` is a joint function of
(a) the elapsed time since `principal.lastAuthAt` and (b) the
resource's `sensitivity` tier.

The age is computed as
`context.now.durationSince(principal.lastAuthAt)`. Because
`durationSince` returns a NEGATIVE duration when its receiver predates
its argument, every comparison must be guarded by
`context.now >= principal.lastAuthAt`. Without that guard, a
pre-authentication request (or a clock-skew situation) silently
satisfies any `< duration("Xh")` test and the policy permits access
that should be denied.

Entities: `Operator` (with `lastAuthAt: datetime`) and `Resource`
(with `sensitivity: Long` in the range [1, 3]). The request context
carries `now: datetime`. Three actions: `read`, `write`, `delete`.

## Requirements

### 1. Fresh Window (age < 1h) -- All Actions, Any Sensitivity

If `context.now >= principal.lastAuthAt` AND
`context.now.durationSince(principal.lastAuthAt) < duration("1h")`,
then the Operator may perform any of `read`, `write`, `delete` on a
Resource of any `sensitivity`.

### 2. Stale Window (1h <= age < 4h) -- Sensitivity-Gated

If the credential is in the stale window
(`duration("1h") <= age < duration("4h")`):

- `read` is permitted regardless of `resource.sensitivity`.
- `write` is permitted ONLY when `resource.sensitivity == 1`.
- `delete` is permitted ONLY when `resource.sensitivity == 1`.

### 3. Expired (age >= 4h) -- No Access

If `context.now.durationSince(principal.lastAuthAt) >= duration("4h")`,
no actions are permitted on any resource.

### 4. Pre-Auth / Clock-Skew (now < lastAuthAt) -- Deny

If `context.now < principal.lastAuthAt`, no actions are permitted.
This is enforced by the `context.now >= principal.lastAuthAt` guard
that every `permit` policy must carry.

## Notes

- All datetimes are in UTC.
- Durations are written in Cedar's Go-style syntax: `duration("1h")`,
  `duration("4h")`. ISO 8601 (`duration("PT1H")`) is rejected by Cedar.
- The `<` boundary at 1h and 4h is strict; a credential whose age is
  exactly `duration("1h")` is in the stale window, not the fresh window.
- The host application is responsible for ensuring `resource.sensitivity`
  is in the documented range [1, 3]; the policy treats only `== 1` as
  "low" for the purposes of stale-window write/delete and treats any
  other value as "not low" (forbidden in the stale window for write/
  delete).
- An equivalent encoding for write/delete is to permit when
  `(age < 4h) && (age < 1h || resource.sensitivity == 1)` -- this is
  logically equivalent and is also accepted by the ceilings.
- A synthesizer that uses an explicit if-then-else chain instead of the
  conjunction-disjunction form is also correct.
