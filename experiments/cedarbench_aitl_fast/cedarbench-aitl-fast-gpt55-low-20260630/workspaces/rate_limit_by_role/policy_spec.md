---
pattern: rate limit by role
difficulty: medium
features:
  - numeric comparison for rate limits
  - role-derived thresholds
  - context-provided counters
domain: API gateway
synthesis_difficulty: 2
---

# Rate Limit by Role -- Policy Specification

## Context

This policy governs access to an API gateway where clients have
tier-based rate limits. Each `ApiClient` belongs to a tier (free,
standard, or premium) which determines the maximum number of requests
allowed per minute. The gateway injects the current request count into
the Cedar context so that the policy can enforce rate ceilings purely
through authorization logic.

## Entities

- **ApiClient** -- the principal. Has a `tier` attribute (String):
  `"free"`, `"standard"`, or `"premium"`.
- **Endpoint** -- the resource. Has an `isPublic` attribute (Bool):
  public endpoints are callable by any tier; non-public endpoints
  require standard or premium tier.

## Actions

- **call** -- invoke a single endpoint.
- **bulkCall** -- invoke an endpoint via the bulk/batch API.

## Context

- `requestsThisMinute` (Long) -- the number of requests the client has
  already made in the current minute window, injected by the gateway
  before the authorization decision.

## Requirements

### 1. Public endpoint access (call)
Any tier (free, standard, premium) may `call` a public endpoint
(`resource.isPublic == true`), subject to tier-specific rate limits:

| Tier       | Rate limit (requestsThisMinute) |
|------------|-------------------------------|
| free       | < 100                         |
| standard   | < 1000                        |
| premium    | unlimited (no cap)            |

### 2. Non-public endpoint access (call)
Only standard and premium clients may `call` a non-public endpoint
(`resource.isPublic == false`). The same rate limits apply:

| Tier       | Rate limit (requestsThisMinute) |
|------------|-------------------------------|
| standard   | < 1000                        |
| premium    | unlimited (no cap)            |

Free-tier clients are never permitted to call non-public endpoints
regardless of their request count.

### 3. Bulk call access (bulkCall)
Only premium clients may use `bulkCall`. The rate limit for bulk
calls is `requestsThisMinute < 500`. Standard and free clients are
never permitted to use `bulkCall`.

## Notes

- The rate limit is a strict less-than comparison: a free client with
  exactly 100 requests this minute is denied.
- Premium clients have no rate limit on `call` but DO have a rate
  limit (< 500) on `bulkCall`.
- The tier attribute is a plain string, not a group membership. There
  is no entity hierarchy for tiers.
- Common failure modes: (a) forgetting to block free-tier from
  non-public endpoints, (b) applying the bulkCall rate limit to call,
  (c) allowing standard clients to bulkCall.
