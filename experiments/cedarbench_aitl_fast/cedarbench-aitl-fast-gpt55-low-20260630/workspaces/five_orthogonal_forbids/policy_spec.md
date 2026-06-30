---
pattern: five orthogonal forbid conditions
difficulty: hard
features:
  - five independent deny conditions composed conjunctively
  - principal attribute gates (blocked, mfaVerified)
  - resource attribute gates (archived, requiresMfa)
  - context attribute gates (outsideBusinessHours, rateLimited)
  - floor / ceiling joint-satisfiability stress (§8.8)
domain: defense in depth / multi-factor access control
synthesis_difficulty: 3
---

# Five Orthogonal Forbids — Policy Specification

## Context

A defense-in-depth access-control policy where five independent
conditions must ALL hold for a request to be permitted. Each condition
is orthogonal: blocking one user does not affect resource archiving,
business-hour windows, MFA requirements, or rate limiting. Real-world
production policies routinely stack 5+ such gates (compliance, security,
operations) and the model under test must compose them conjunctively
without dropping any one.

## Entities

- `User` with attributes:
  - `isBlocked: Bool` — set by abuse / security teams
  - `mfaVerified: Bool` — current session has fresh MFA proof
- `Resource` with attributes:
  - `isArchived: Bool` — moved to cold storage, no longer mutable
  - `requiresMfa: Bool` — owner-tagged sensitive resource

## Action

- `access` — generic access action over `Resource`

## Context

- `now: datetime` — current request time (informational)
- `outsideBusinessHours: Bool` — pre-computed by the host
- `rateLimited: Bool` — pre-computed by the rate limiter

## Requirements

A `User` may `access` a `Resource` only when ALL of the following hold:

1. **Not blocked.** `!principal.isBlocked`.
2. **Not archived.** `!resource.isArchived`.
3. **MFA gate satisfied.** Either the resource does not require MFA,
   or the principal has MFA verified for this session
   (`!resource.requiresMfa || principal.mfaVerified`).
4. **Business hours.** `!context.outsideBusinessHours`.
5. **Not rate-limited.** `!context.rateLimited`.

If any one of the five conditions fails, access is denied.

### Default Deny

All requests not matching the above are denied.
