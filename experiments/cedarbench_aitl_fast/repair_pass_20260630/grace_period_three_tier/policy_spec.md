---
pattern: grace period three-tier
difficulty: hard
features:
  - datetime offset arithmetic
  - Go-style duration literals
  - four-tier temporal partition
  - tier-boundary inclusive/exclusive bounds
domain: PKI / TLS infrastructure
synthesis_difficulty: 3
---

# Grace Period Three-Tier — Policy Specification

## Context

This policy governs how a Service accepts connections from a Subscriber
that presents an expiring TLS client certificate. Rather than a hard
expiration cutoff, the Service models a four-tier lifecycle that gives
operators time to renew without breaking traffic abruptly.

Entities:

- `Subscriber` with attribute `certExpiresAt: datetime` — the wall-clock
  instant at which the subscriber's certificate expires.
- `Service` (no attributes).

Context (on every action): `now: datetime` — the current wall-clock
instant, populated by the Service from its trusted clock at request time.

Three actions, each corresponding to a specific tier of the lifecycle:
`connect`, `connectWithWarning`, `connectInGrace`.

## Lifecycle tiers

The certificate's `certExpiresAt` partitions the timeline into four
contiguous, non-overlapping tiers. Boundaries use the convention that
the tier-end is **exclusive** and the tier-start is **inclusive** (i.e.
half-open intervals `[start, end)`).

| Tier | Interval                                                 | Permitted action       |
|------|----------------------------------------------------------|------------------------|
| 1    | `now < certExpiresAt - 7d`                               | `connect`              |
| 2    | `certExpiresAt - 7d <= now < certExpiresAt`              | `connectWithWarning`   |
| 3    | `certExpiresAt <= now < certExpiresAt + 30d`             | `connectInGrace`       |
| 4    | `now >= certExpiresAt + 30d`                             | (none — all denied)    |

## Requirements

### 1. Pre-Warning Tier (tier 1) — `connect`

A `Subscriber` may perform `connect` on a `Service` if and only if
`context.now < principal.certExpiresAt.offset(duration("-7d"))`.

`connect` is NOT permitted in tiers 2, 3, or 4.

### 2. Warning Tier (tier 2) — `connectWithWarning`

A `Subscriber` may perform `connectWithWarning` on a `Service` if and
only if both:

- `context.now >= principal.certExpiresAt.offset(duration("-7d"))`, AND
- `context.now < principal.certExpiresAt`.

`connectWithWarning` is NOT permitted in tiers 1, 3, or 4.

### 3. Grace Tier (tier 3) — `connectInGrace`

A `Subscriber` may perform `connectInGrace` on a `Service` if and only
if both:

- `context.now >= principal.certExpiresAt`, AND
- `context.now < principal.certExpiresAt.offset(duration("30d"))`.

`connectInGrace` is NOT permitted in tiers 1, 2, or 4. The host
application is responsible for emitting an audit-log entry whenever a
grace-tier connection is permitted.

### 4. After-Grace Tier (tier 4) — All denied

When `context.now >= principal.certExpiresAt.offset(duration("30d"))`,
all three actions (`connect`, `connectWithWarning`, `connectInGrace`)
MUST be denied. Cedar's default-deny semantics suffice for this tier;
no explicit `forbid` is required.

## Notes

- All temporal arithmetic uses Cedar's `datetime.offset(duration(...))`.
  Cedar duration literals are **Go-style** (`"7d"`, `"-7d"`, `"30d"`,
  `"1h30m"`), NOT ISO 8601 (`"P7D"`, `"PT24H"` are rejected).
- `datetime` literals are ISO 8601 (`"2025-03-02T20:00:00Z"`).
- Tier boundaries are **half-open**: the upper end is strict (`<`), the
  lower end is inclusive (`>=`). Mixing these up produces off-by-one
  failures at tier transitions where a candidate either double-permits
  the boundary instant or denies it entirely.
- Tiers are mutually exclusive across actions: at any concrete
  `(now, certExpiresAt)` pair, at most one of the three actions is
  permitted.
- Negative durations are written as `duration("-7d")`. Cedar accepts
  the leading minus sign on duration literals.
