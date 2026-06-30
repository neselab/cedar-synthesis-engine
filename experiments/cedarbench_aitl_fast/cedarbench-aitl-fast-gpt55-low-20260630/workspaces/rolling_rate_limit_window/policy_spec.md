---
pattern: rolling rate limit window
difficulty: medium
features:
  - dual-window numeric comparison (per-minute AND per-hour)
  - cost-multiplier-adjusted budget arithmetic
  - context-supplied rolling-window counters
  - tier-derived thresholds
domain: API gateway
synthesis_difficulty: 3
---

# Rolling Rate Limit Window -- Policy Specification

## Context

This policy governs an API gateway that enforces a rolling-window rate
limit. Unlike a fixed-window limit (which resets at the top of every
minute), the gateway tracks the number of requests each client has
issued in the **last 60 seconds** and the **last 60 minutes**, both
measured as a sliding window from "now". The gateway computes both
counters and injects them into the Cedar context before the
authorization decision.

The `bulkCall` action is more expensive: each endpoint declares a
`costMultiplier` (Long), and the effective bulk-call budget is
`requestsLastMinute * resource.costMultiplier`. This is bounded by a
tier-specific cap.

## Entities

- **Client** -- the principal. Has a `tier` attribute (String):
  `"free"`, `"pro"`, or `"enterprise"`.
- **Endpoint** -- the resource. Has a `costMultiplier` attribute
  (Long, must satisfy `1 <= costMultiplier <= 100`). The cost
  multiplier inflates the effective request count for `bulkCall`
  budget arithmetic.

## Actions

- **call** -- invoke a single endpoint.
- **bulkCall** -- invoke a batched/bulk endpoint operation.

## Context

For both actions:
- `requestsLastMinute` (Long) -- rolling-window count over the last 60
  seconds. Bounded `0 <= requestsLastMinute <= 1000000`.
- `requestsLastHour` (Long) -- rolling-window count over the last 60
  minutes. Bounded `0 <= requestsLastHour <= 1000000`.
- `windowExpired` (Bool) -- true if the rolling-window snapshot is
  stale (older than 1 second) and must be rejected.

## Requirements

### 1. call action
A `call` is permitted only when `windowExpired == false` AND the
tier-specific dual-window limit is satisfied:

| Tier        | requestsLastMinute | requestsLastHour |
|-------------|--------------------|------------------|
| free        | < 60               | < 1000           |
| pro         | < 600              | < 10000          |
| enterprise  | unlimited          | unlimited        |

(Both per-minute AND per-hour bounds must be satisfied for free and
pro; enterprise has no rate limit on `call`.)

### 2. bulkCall action
A `bulkCall` is permitted only when `windowExpired == false`,
`1 <= resource.costMultiplier <= 100`,
`0 <= context.requestsLastMinute <= 1000000`, AND the tier-specific
cost-adjusted budget is satisfied:

| Tier        | requestsLastMinute * costMultiplier |
|-------------|-------------------------------------|
| free        | <= 100                              |
| pro         | <= 1000                             |
| enterprise  | unlimited (still requires fresh window) |

The bound guards (`1..100` on costMultiplier, `0..1_000_000` on
requestsLastMinute) keep the product within Cedar's Long range and
must be checked explicitly before the multiplication.

## Notes

- The `windowExpired` flag is a kill-switch: if true, NO action of
  any tier is permitted -- not even enterprise. The gateway is
  expected to refresh and re-attempt.
- Rate-limit comparisons for `call` are strict less-than; the
  cost-budget comparison for `bulkCall` is non-strict (<=).
- The tier attribute is a plain string, not group membership.
- Common failure modes:
    (a) ignoring `windowExpired` for the enterprise tier,
    (b) applying only the per-minute or only the per-hour limit (not
        both),
    (c) skipping the costMultiplier-bound guards and getting
        symcc-level overflow noise,
    (d) using strict `<` instead of `<=` for the bulkCall budget.
