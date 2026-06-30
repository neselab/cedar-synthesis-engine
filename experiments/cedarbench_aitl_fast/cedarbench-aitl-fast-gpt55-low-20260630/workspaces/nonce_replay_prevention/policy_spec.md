---
pattern: nonce-based replay prevention
difficulty: medium
features:
  - optional context attribute (has-guard required)
  - Set<String> membership on resource
  - three-state distinction (missing / invalid / valid)
domain: API security
synthesis_difficulty: 3
---

# Nonce Replay Prevention -- Single-Use Token Authorization

## Context

This scenario models a critical API endpoint that requires per-request
nonce verification to prevent replay attacks. Each `CriticalEndpoint`
maintains a `validNonces` set: nonces that have been issued recently by
the platform and have not yet been consumed by a successful invocation.

When a `User` invokes the endpoint, the request may include a `nonce`
in its context. The authorization decision must distinguish three
distinct states:

1. **Nonce missing** -- `context` does NOT have a `nonce` attribute.
   The request carries no proof of recency. **Deny.**
2. **Nonce present but invalid** -- `context.nonce` is set but is NOT in
   `resource.validNonces`. This indicates either a replayed nonce
   (already consumed) or a forged value. **Deny.**
3. **Nonce present and valid** -- `context.nonce` is set AND is in
   `resource.validNonces`. The nonce proves request recency and
   uniqueness. **Permit.**

## Schema

- Entity `User` -- caller identity (no attributes used for authorization).
- Entity `CriticalEndpoint` with `validNonces: Set<String>` -- the set
  of nonces currently considered valid for this endpoint.
- Action `invoke` applying `User` -> `CriticalEndpoint`.
- Context attribute `nonce: String` declared optional (`?`) -- the
  request may or may not carry a nonce.

## Requirements

### Action: invoke

The invoke action is permitted ONLY when BOTH:

1. The request context has a `nonce` attribute (`context has nonce`).
2. The endpoint's `validNonces` set contains that nonce
   (`resource.validNonces.contains(context.nonce)`).

Cedar idiom (note the has-guard before the read):

```
permit (
    principal is User,
    action == Action::"invoke",
    resource is CriticalEndpoint
)
when {
    context has nonce && resource.validNonces.contains(context.nonce)
};
```

The has-guard is mandatory: reading `context.nonce` without first
guarding on `context has nonce` is rejected by Cedar's type-checker
when the attribute is optional in the schema.

### Floors

- **Valid nonce permits invoke.** A request whose context.nonce is in
  the endpoint's validNonces MUST be permitted.

### Negative requirements (encoded by ceiling)

- A request with no nonce in context MUST NOT be permitted.
- A request whose context.nonce is NOT in validNonces MUST NOT be
  permitted.

### Liveness

The invoke action must permit at least one request.

## Out of scope

- No nonce-issuance flow, no nonce expiry timestamps.
- No principal-side authorization beyond nonce check (any User may
  invoke if they present a valid nonce).
- No replay-detection bookkeeping (the set's mutation is the host
  app's responsibility, not the policy's).
