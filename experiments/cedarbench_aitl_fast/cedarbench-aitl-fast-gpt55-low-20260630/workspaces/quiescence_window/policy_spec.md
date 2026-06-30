---
pattern: quiescence-window rate limit
difficulty: medium
features:
  - datetime
  - duration
  - durationSince
  - sign-guard
domain: rate-limiting
synthesis_difficulty: 3
---

# Quiescence Window — per-user cooldown

## Background

Many APIs and applications enforce rate limiting in the simplest form
possible: after a user performs a sensitive action, they must wait some
quiescence window before performing it again. This is sometimes called a
"cooldown" or "settling period." Examples include funds transfers, password
reset requests, posting to a forum, sending invites, and re-trying a
withdrawn vote.

Cedar's `datetime` and `duration` extensions are the natural primitive
for expressing this rule. The window is computed as the time between the
user's previous successful action and the current request.

## Entities

- `User` — has `lastActionAt: datetime` recording when the user last
  performed the action. The host application updates this attribute on
  every successful permit.
- `Resource` — opaque target of the action.

## Action

- `performAction` (principal `User`, resource `Resource`) — context
  supplies the current wall-clock time as `now: datetime`.

## Authorization rules

`performAction` is permitted only when the elapsed time between
`principal.lastActionAt` and `context.now` strictly exceeds **1 hour**.

The Cedar encoding is:

```
context.now.durationSince(principal.lastActionAt) > duration("1h")
```

### Sign guard

`durationSince` returns a signed duration: when the supplied "since"
timestamp is **after** `now`, the result is negative. A naive policy that
only checks `> duration("1h")` is correct on its own, because no negative
duration exceeds a positive 1-hour window. However, the spec REQUIRES that
policies also verify `context.now >= principal.lastActionAt`, defending
against clock-skew bugs that would surface as silent permits if the
duration encoding ever changed (e.g. an unsigned variant). This guard is
explicit and load-bearing — without it, the ceiling check is technically
correct but brittle.

The combined guard is:

```
context.now >= principal.lastActionAt
&& context.now.durationSince(principal.lastActionAt) > duration("1h")
```

## What the verification plan checks

1. **Ceiling** — `performAction` MUST be denied unless both the
   sign-guard holds AND more than 1 hour has elapsed since the last action.
2. **Floor 1 — fresh user** — when `now - lastActionAt = 2h` (well past
   the cooldown), the action MUST be permitted.
3. **Floor 2 — far-future cooldown** — when `now - lastActionAt = 24h`,
   the action MUST be permitted (sanity bound for large windows).
4. **Liveness** — at least one `User + performAction + Resource` request
   must be permitted.

## Out of scope

- Per-resource cooldowns (this scenario uses a per-user cooldown).
- Bursting / token-bucket dynamics — see `rate_limit_by_role` for a
  different style of rate limit.
