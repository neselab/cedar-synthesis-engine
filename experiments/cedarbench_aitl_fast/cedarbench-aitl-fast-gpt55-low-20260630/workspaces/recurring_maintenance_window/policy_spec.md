---
pattern: recurring maintenance window
difficulty: hard
features:
  - datetime arithmetic
  - duration offset
  - host-supplied recurring window boundaries
  - role-based override
domain: infrastructure / SRE
synthesis_difficulty: 3
---

# Recurring Maintenance Window -- Policy Specification

## Context

This policy governs access to a production system that has a recurring
maintenance window (for example, every Sunday 02:00-04:00 UTC). During
the window, the system takes ordinary user traffic offline so the admin
team can perform scheduled operations; ordinary users are locked out.
Oncall engineers and admins retain access at all times so they can
respond to incidents.

### Why the host app supplies the window boundaries

Cedar has no modulo operator on `datetime`, so a policy cannot compute
"what part of the weekly cycle are we in?" on its own. Instead, the host
application is responsible for pre-computing the boundaries of the
currently-active window, or a sentinel if no window is active.

The host supplies three context fields on every request:

- `context.now: datetime` -- the current wall-clock time.
- `context.windowStart: datetime` -- the start of the current window.
  If no maintenance window is currently active, the host supplies a
  far-past sentinel datetime and a zero duration below.
- `context.windowDuration: duration` -- the length of the window
  (e.g. `duration("2h")`). The host supplies `duration("0s")` when no
  window is active.

The predicate "the request is inside the maintenance window" is then:

```
context.now >= context.windowStart
&& context.now < context.windowStart.offset(context.windowDuration)
```

Equivalently, "outside the window":

```
context.now < context.windowStart
|| context.now >= context.windowStart.offset(context.windowDuration)
```

### Entities and actions

- `User` has a `role: String` that is exactly one of `"user"`,
  `"oncall"`, or `"admin"`.
- `System` is the resource.
- Actions: `access` (ordinary system access) and `adminOperation`
  (privileged administrative work that must happen during maintenance).

## Requirements

### 1. User Access Outside Window (Permit)

- A `User` whose `role` is `"user"` may perform `access` on a `System`
  ONLY when the current time is outside the maintenance window, i.e.
  `context.now < context.windowStart` OR `context.now >=
  context.windowStart.offset(context.windowDuration)`.
- Ordinary users MUST be blocked from `access` during the maintenance
  window.

### 2. Oncall and Admin Anytime Access (Permit)

- A `User` whose `role` is `"oncall"` may perform `access` on a
  `System` at any time, with no window restriction.
- A `User` whose `role` is `"admin"` may perform `access` on a
  `System` at any time, with no window restriction.

### 3. Admin-Only In-Window Operations (Permit)

- A `User` whose `role` is `"admin"` may perform `adminOperation` on a
  `System` ONLY when the current time is inside the maintenance window,
  i.e. `context.now >= context.windowStart` AND `context.now <
  context.windowStart.offset(context.windowDuration)`.
- Only admins may perform `adminOperation`. Ordinary users and oncall
  engineers are never permitted to perform `adminOperation`, regardless
  of the time.

### 4. Admin Operations Outside Window -- Forbidden

- Even an admin may NOT perform `adminOperation` outside the maintenance
  window. `adminOperation` is reserved for the scheduled maintenance
  period so that its side effects cannot surprise users during normal
  operation.

## Notes

- `context.now` and `context.windowStart` are Cedar `datetime` values.
  Literal syntax is ISO 8601, e.g. `datetime("2025-03-02T20:00:00Z")`.
- `context.windowDuration` is a Cedar `duration`. Its literal syntax is
  Go-style (e.g. `duration("2h")`, `duration("30m")`, `duration("0s")`);
  ISO 8601 duration literals (`"PT2H"`) are REJECTED by Cedar.
- Use `.offset(duration)` to compute the window end:
  `windowStart.offset(windowDuration)` is the first instant outside the
  window. The comparison on the right edge is strict (`<`), so a request
  exactly at the end instant is considered outside the window.
- Cedar supports `<`, `<=`, `>`, `>=` directly on `datetime` values.
- When no window is active, the host supplies a far-past `windowStart`
  together with `windowDuration == duration("0s")`. In that case the
  window-end offset equals `windowStart`, so the "inside the window"
  predicate `now >= windowStart && now < windowStart` is unsatisfiable,
  correctly making every request "outside the window."
- Cedar denies by default, so the absence of a permit for ordinary
  users during the window, or for non-admin `adminOperation`, is
  sufficient to deny. An explicit forbid for out-of-window
  `adminOperation` provides defense-in-depth.
- The role values are exactly `"user"`, `"oncall"`, and `"admin"`. No
  other roles exist in this system.
