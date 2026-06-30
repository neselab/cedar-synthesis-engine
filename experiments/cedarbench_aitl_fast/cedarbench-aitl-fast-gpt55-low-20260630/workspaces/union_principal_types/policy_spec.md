---
pattern: union principal types
difficulty: hard
features:
  - principal type union (User | ApiKey | ServiceAccount)
  - is-typed type narrowing
  - per-type attribute access
  - heterogeneous principal authorization
domain: api gateway
synthesis_difficulty: 3
---

# Union Principal Types — API Gateway

## Background

An API gateway accepts inbound requests on a single action `callApi`, but the
caller can be any of three different principal kinds:

- A human `User` (interactive console / SDK with an auth token), with an
  `mfaVerified: Bool` attribute.
- An `ApiKey` (machine-to-machine bearer credential), with a `scopes:
  Set<String>` attribute listing capability strings.
- A `ServiceAccount` (an internal first-party service), with a
  `serviceName: String` identifier.

The action is declared with a *principal-type union* in `appliesTo`:

```
callApi appliesTo {
    principal: [User, ApiKey, ServiceAccount],
    resource: [Resource],
    context: {}
};
```

Each principal kind has *different attributes*, so the policy must
discriminate on principal type before reading any kind-specific field.
This is the canonical use of Cedar's `is`-typed narrowing in `when` clauses:
`principal is User && principal.mfaVerified` is well-typed because the
left conjunct narrows the type before the attribute read.

## Authorization rule

`callApi` is permitted on `Resource` exactly when the principal is one of:

1. A `User` with `mfaVerified == true`.
2. An `ApiKey` whose `scopes` set contains the string `"api_call"`.
3. A `ServiceAccount` with a non-empty `serviceName` (i.e.
   `serviceName != ""`).

If none of these hold the request is denied (default-deny).

## Notes for implementers

- Do NOT read `principal.mfaVerified` without a `principal is User` guard;
  Cedar's validator will reject it (the attribute does not exist on
  `ApiKey` or `ServiceAccount`).
- Use the type-narrowing idiom: `principal is T && principal.attr ...`
  inside a single conjunction.
- The three branches are independent — a `User` without MFA must be
  denied even if some other principal type would have been allowed.
