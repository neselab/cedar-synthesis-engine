---
pattern: stale cache invalidation
difficulty: hard
features:
  - duration freshness windows
  - optional context attributes
  - has-guards on optional timestamps
  - role-based MFA escalation
domain: security / authorization caching
synthesis_difficulty: 4
---

# Stale Cache Invalidation -- Policy Specification

## Context

This policy governs an authorization service that caches authentication
decisions to reduce load on the identity provider. Cached authentication
becomes "stale" after a configurable window: low-risk reads tolerate a
generous window, while higher-risk write or delete actions require a
much fresher attestation. The policy enforces three different staleness
windows tied to action sensitivity, and additionally requires a fresh
out-of-band MFA attestation for the most destructive action.

Entities: `User` (with `role: String`) and `Resource`. The context
carries the current request time `now: datetime`, plus two OPTIONAL
timestamps populated by the host application:
- `authCacheTimestamp?: datetime` — the moment when the cached auth
  decision was issued. Absent if there is no cache hit (the host then
  refuses the request before reaching the policy, but the policy MUST
  also refuse defensively).
- `mfaTimestamp?: datetime` — the moment of the user's most recent
  successful MFA challenge. Absent if the user has never completed
  MFA (or it has expired and been purged).

Three actions: `read`, `writeCritical`, and `delete`.

## Requirements

### 1. Read with cached auth (Permit)
- A User may perform the `read` action on a Resource ONLY when:
  - `context.authCacheTimestamp` is present, AND
  - `context.now.durationSince(context.authCacheTimestamp) < duration("5m")`
    (the cache is no more than 5 minutes old).
- Role does not matter for `read`. Any user with a fresh enough cache
  may read.

### 2. WriteCritical with fresh cache (Permit)
- A User may perform the `writeCritical` action on a Resource ONLY when:
  - `context.authCacheTimestamp` is present, AND
  - `context.now.durationSince(context.authCacheTimestamp) < duration("60s")`
    (the cache is no more than 60 seconds old — much stricter than read).
- Role does not matter for `writeCritical`. Any user with a sufficiently
  fresh cache may write.

### 3. Delete with fresh MFA (Permit)
- A User may perform the `delete` action on a Resource ONLY when ALL of:
  - The user's role is `"admin"`, AND
  - `context.mfaTimestamp` is present, AND
  - `context.now.durationSince(context.mfaTimestamp) < duration("30s")`
    (MFA was completed within the last 30 seconds).
- Note: `delete` does NOT consult `authCacheTimestamp`. Delete bypasses
  the auth cache entirely and demands a fresh MFA attestation. This is
  by design — destructive actions must not piggy-back on cached auth.

## Notes
- `authCacheTimestamp` and `mfaTimestamp` are declared `?` in the
  schema (optional). Every read of either MUST be guarded by `context
  has ...` first, per Cedar's optional-attribute discipline.
- Cedar denies by default. Absence of a permit is sufficient to refuse
  a stale or unattested request; no explicit forbids are required.
- All durations are positive: `now > authCacheTimestamp` and
  `now > mfaTimestamp` are presumed by the host application's clock
  invariants. The policy does not need to handle clock skew.
- Role values for `delete` are exactly `"admin"`. Other roles never
  pass the delete ceiling.
- The freshness windows are intentionally tight to make the per-action
  thresholds independently observable: 5 minutes vs. 60 seconds vs. 30
  seconds with a separate timestamp.
