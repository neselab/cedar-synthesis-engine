---
pattern: Action with many principal types (is-narrowing across N types)
difficulty: medium
features:
  - single action with 6 principal entity types in appliesTo
  - per-type `is` narrowing required to read type-specific attributes
  - heterogeneous attributes across principal types
  - disjunctive ceiling that composes 6 type-specific predicates
domain: API platform / universal gateway
synthesis_difficulty: 3
---

# Universal API Gateway — Policy Specification

## Context

A universal API gateway exposes a single action, `invoke`, which can be
called by six different kinds of caller. Each caller is modeled as a
distinct Cedar entity type with its own authentication signal:

- `User` — a human caller; authenticated via MFA.
- `ApiKey` — a long-lived programmatic key; carries a scope set.
- `ServiceAccount` — a named workload identity; identified by service name.
- `Webhook` — an inbound webhook delivery; authenticated by HMAC signature.
- `BatchJob` — a pre-vetted batch job emitted by the orchestrator.
- `Scheduler` — a cron trigger; authenticated by the scheduler control plane.

All six principal types appear in `invoke.appliesTo.principal`. Each
type carries different attributes, so the policy must use Cedar's
`is`-narrowing (`principal is User && principal.mfaVerified`, etc.) to
read each attribute only after the type has been pinned.

This scenario tests whether the synthesized policy correctly handles
`is`-narrowing across N=6 distinct principal types in a single action.

## Requirements

### 1. User — MFA verified
A `User` may `invoke` a `Resource` when `principal.mfaVerified == true`.

### 2. ApiKey — invoke scope present
An `ApiKey` may `invoke` a `Resource` when its `scopes` set contains
`"invoke"`.

### 3. ServiceAccount — non-empty service name
A `ServiceAccount` may `invoke` a `Resource` when its `serviceName` is
not the empty string.

### 4. Webhook — valid signature
A `Webhook` may `invoke` a `Resource` when `principal.signatureValid == true`.

### 5. BatchJob — always permitted
Any `BatchJob` may `invoke` a `Resource`. The orchestrator pre-vets the
job before emitting it, so no per-request gate is needed at the policy
layer.

### 6. Scheduler — cron verified
A `Scheduler` may `invoke` a `Resource` when `principal.cronVerified == true`.

### 7. Default Deny
All other requests are denied. In particular:
- A `User` without `mfaVerified` is denied.
- An `ApiKey` whose `scopes` does not contain `"invoke"` is denied.
- A `ServiceAccount` with an empty `serviceName` is denied.
- A `Webhook` with `signatureValid == false` is denied.
- A `Scheduler` with `cronVerified == false` is denied.
