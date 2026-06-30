---
pattern: composed duration arithmetic with sign guards
difficulty: hard
features:
  - duration arithmetic
  - duration.toMilliseconds()
  - datetime.durationSince()
  - sign-guarded comparisons
  - cumulative quota tracking
domain: subscription / grace-period billing
synthesis_difficulty: 4
---

# Composed Duration Arithmetic -- Policy Specification

## Context

This policy governs `accessWithGrace` requests against a `Resource` for
users in the middle of a 90-day cumulative grace period. Each `User`
carries:

- `graceStart: datetime` -- when the grace window opened.
- `graceQuotaUsed: duration` -- how much grace time has been consumed
  in PREVIOUS sessions.

At request time the host supplies `context.now`, and the policy must
admit access only if the cumulative grace consumption (previously-used
quota plus the elapsed time of the current session) is still inside the
90-day budget.

## Cedar duration facts

Cedar's `duration` type does **not** support `+` or `-` directly.
Writing `duration("90d") - principal.graceQuotaUsed` is a type error
("expected Long but saw duration"), as is
`principal.graceQuotaUsed + context.now.durationSince(...)`.

The supported composition path is to drop into `Long` via
`d.toMilliseconds()` and do the arithmetic on millisecond counts:

```
principal.graceQuotaUsed.toMilliseconds()
  + context.now.durationSince(principal.graceStart).toMilliseconds()
  <= duration("90d").toMilliseconds()
```

Cedar's type system does NOT constrain `duration` to be non-negative,
and `datetime.durationSince(other)` returns a negative duration when
`other > self`. Both must be sign-guarded explicitly or the budget
check is meaningless (a negative `durationSince` would let an attacker
who lies about `now` -- or whose clock is skewed earlier than
`graceStart` -- bypass the budget regardless of `graceQuotaUsed`).

## Requirements

### 1. accessWithGrace ceiling

A User may perform `accessWithGrace` on a Resource ONLY IF all of the
following hold:

- `context.now >= principal.graceStart` (the current session is not
  occurring before the grace window opened).
- `principal.graceQuotaUsed.toMilliseconds() >= 0` (the consumed quota
  is non-negative).
- `principal.graceQuotaUsed.toMilliseconds() +
   context.now.durationSince(principal.graceStart).toMilliseconds() <=
   duration("90d").toMilliseconds()`
  (the cumulative grace consumption fits inside the 90-day budget).

There are no other actions; Cedar's deny-by-default disposes of every
other request shape.

### 2. Floors (positive obligations)

- **Fresh grace.** A User whose `context.now == principal.graceStart`
  AND whose `principal.graceQuotaUsed == duration("0d")` MUST be
  permitted.
- **Well within budget.** A User satisfying the sign guards above whose
  `graceQuotaUsed.toMilliseconds() +
   now.durationSince(graceStart).toMilliseconds() <=
   duration("30d").toMilliseconds()` (a third of the budget) MUST be
   permitted.

### 3. Liveness

The policy must permit at least one (User, accessWithGrace, Resource)
request -- the candidate cannot collapse to `forbid` or to a vacuous
`when { false }` permit.

## Notes

- `duration("0d")` is the canonical zero. `duration("0s")` would also
  work but the spec uses day-granularity throughout.
- `duration.toMilliseconds()` returns Cedar `Long` (i64 milliseconds).
  90 days fits comfortably (~7.78e9 ms), so overflow is not a concern.
- Cedar denies by default, so no explicit `forbid` is needed for
  out-of-budget requests, missing sign guards, or other actions.
