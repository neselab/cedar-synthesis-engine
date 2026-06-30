---
pattern: age verification with leap-year edge cases
difficulty: hard
features:
  - datetime arithmetic
  - duration comparison
  - leap-year correctness
  - per-resource age threshold
domain: media / age-gated content
synthesis_difficulty: 4
---

# Age Verification with Leap Years -- Policy Specification

## Context

This policy governs access to age-gated content (videos, purchases,
subscriptions) where each resource declares a minimum age in years and
each user has a date of birth. The host must verify the user is at
least that many years old at the time of the request.

The wrinkle: Cedar's `duration` type only supports day-granularity
arithmetic (`duration("Xd")`), and Cedar does NOT support arbitrary
expressions inside the `duration()` constructor — only string literals.
You cannot write `duration(toString(years * 365) + "d")`. Therefore,
naive year-to-day conversion (`years * 365`) under-counts leap days
and would let a user view 18+ content up to 5 days before their 18th
birthday.

The correct encoding enumerates the supported `minAgeYears` values
(13, 18, 21) and uses a hand-computed conservative day threshold for
each that accounts for the maximum number of leap days that could
fall in any contiguous span of that many years.

Entities: `User` (with `dateOfBirth: datetime`), `Content` (with
`minAgeYears: Long`). Context: `now: datetime`.

Actions: `view`, `purchase`, `subscribe`. All three actions enforce
the same age threshold against `resource.minAgeYears`.

## Day thresholds (hand-computed)

For each supported age, the maximum number of leap days in any
contiguous N-year span is `floor(N/4) + 1` in the worst case
(when the span starts just before a leap year):
- N=13: up to 4 leap days  ->  conservative threshold = 13*365 + 3 = **4748 days**
- N=18: up to 5 leap days  ->  conservative threshold = 18*365 + 5 = **6575 days**
- N=21: up to 6 leap days  ->  conservative threshold = 21*365 + 5 = **7670 days**

These thresholds are deliberately tuned so that any user who is at
least `threshold` days older than `now` is *guaranteed* to be at least
`minAgeYears` years old in calendar terms. They are also tight enough
that floors using the same threshold do not over-restrict legitimate
adult users beyond the documented bound.

## Requirements

### 1. View Age Gate (Permit)
- A User may perform the `view` action on a Content resource ONLY IF:
  - `resource.minAgeYears == 13` AND
    `context.now.durationSince(principal.dateOfBirth) >= duration("4748d")`, OR
  - `resource.minAgeYears == 18` AND
    `context.now.durationSince(principal.dateOfBirth) >= duration("6575d")`, OR
  - `resource.minAgeYears == 21` AND
    `context.now.durationSince(principal.dateOfBirth) >= duration("7670d")`.
- Content with any other `minAgeYears` value is unsupported and the
  view action MUST be denied for it.

### 2. Purchase Age Gate (Permit)
- A User may perform the `purchase` action on a Content resource under
  the same enumerated age conditions as `view`.

### 3. Subscribe Age Gate (Permit)
- A User may perform the `subscribe` action on a Content resource under
  the same enumerated age conditions as `view`.

### 4. Floors
- A User whose `dateOfBirth` is at least 6575 days before `context.now`
  MUST be permitted to `view` Content where `minAgeYears == 18`.
- A User whose `dateOfBirth` is at least 7670 days before `context.now`
  MUST be permitted to `purchase` Content where `minAgeYears == 21`.
- A User whose `dateOfBirth` is at least 4748 days before `context.now`
  MUST be permitted to `view` Content where `minAgeYears == 13`.

## Notes
- Cedar denies by default, so the absence of a permit for under-age
  users is sufficient. No explicit forbid is required.
- The conservative day thresholds slightly over-restrict (by a couple
  of days near the user's birthday) but never under-permit. This is the
  intended trade-off: regulatory exposure favors over-restriction.
- The floor thresholds match the ceiling thresholds exactly, so a user
  at the threshold is guaranteed to satisfy the ceiling.
- Cedar duration literals use Go-style syntax: `duration("6575d")` is
  6575 days. ISO 8601 (`"P6575D"`) is rejected.
