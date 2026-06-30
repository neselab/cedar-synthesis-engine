---
pattern: business hours with user-supplied timezone offset
difficulty: hard
features:
  - datetime arithmetic
  - duration comparison for time-of-day
  - per-principal timezone offset
  - datetime.offset and datetime.toTime
domain: enterprise / HR
synthesis_difficulty: 3
---

# Business Hours with User-Supplied Timezone Offset -- Policy Specification

## Context

This policy governs access to an enterprise system. Each employee
carries a `timezoneOffset` attribute (a Cedar `duration`) representing
their local timezone's offset from UTC. The host application supplies
the current wall-clock time as a UTC `datetime` (`context.now`).

The employee's local time-of-day is computed by offsetting the
supplied UTC datetime by the employee's timezone offset and then
extracting the time-of-day component:

```
context.now.offset(principal.timezoneOffset).toTime()
```

`datetime.offset(duration)` returns a new `datetime` shifted by the
given duration. `datetime.toTime()` returns the time-of-day as a
`duration` in the range `[duration("0h"), duration("24h"))`.

Entities: `Employee` (with `timezoneOffset: duration`) and `System`.

Two actions: `access` (general system access, business hours only)
and `report` (report submission, any time).

## Requirements

### 1. Business-Hours Access (Permit)
- An `Employee` may perform the `access` action on a `System` resource
  ONLY when their local time-of-day is within business hours, defined
  as 9:00 (inclusive) through 17:00 (exclusive) local time.
- Specifically: `context.now.offset(principal.timezoneOffset).toTime()
  >= duration("9h")` AND `context.now.offset(principal.timezoneOffset).toTime()
  < duration("17h")`.
- Outside of these local business hours, `access` is denied.

### 2. Report Submission (Permit)
- An `Employee` may perform the `report` action on a `System` resource
  at any time of day, regardless of timezone or local time-of-day.

## Notes

- `timezoneOffset` is a Cedar `duration`. Cedar durations use Go-style
  syntax: `duration("-8h")`, `duration("5h30m")`, `duration("0h")`.
  ISO 8601 duration syntax (`PT8H`) is NOT accepted.
- `context.now` is a Cedar `datetime` in UTC. Cedar datetimes use ISO
  8601 syntax: `datetime("2025-03-02T14:00:00Z")`.
- `datetime.offset(duration)` shifts the datetime by the given
  duration (positive or negative) and returns a new `datetime`.
- `datetime.toTime()` returns the time-of-day component of a datetime
  as a `duration` in the range `[duration("0h"), duration("24h"))`.
- Both 9:00 and 17:00 boundaries: 9:00 is INSIDE business hours
  (>=); 17:00 is OUTSIDE (strict <).
- Cedar denies by default; the absence of a permit for `access`
  outside of business hours is sufficient.
- The two actions are completely orthogonal: `access` is gated by
  local business hours, `report` is unrestricted.
