---
pattern: revocation cascade and reinstatement
difficulty: hard
features:
  - parent revocation cascading to derived permissions
  - host-precomputed chain attestation (Cedar cannot quantify over Sets)
  - owner bypass with attestation conjunction
domain: collaborative document sharing / delegated permissions
synthesis_difficulty: 3
---

# Revocation Cascade & Reinstatement — Policy Specification

## Context

This policy implements **cascading revocation** of derived permissions.
A `Resource` has an `owner`. The owner may grant access to other users,
who in turn may re-grant access to further users, forming a **delegation
chain** rooted at the owner.

When any link in the chain is revoked, **all downstream derived
permissions cascade-invalidate**. A user holding a derived permission
loses access the moment any ancestor grant in the chain is revoked,
even if their own immediate grantor has not personally revoked them.

Cedar cannot enumerate over arbitrary set elements (it has no universal
or existential quantifier on `Set<...>`). The host application is
therefore responsible for walking the grant chain that led to the
current request and pre-computing two boolean attestations into the
request context:

- `accessAuthorized` — every link in the chain is currently active
  (a complete, valid delegation path exists from owner to principal).
- `revocationDetected` — at least one link in the chain has been
  revoked. If true, the cascade invalidates this principal's derived
  permission.

The Cedar policy then composes these attestations with the owner
bypass.

## Entities

- **User** — opaque principal identity (no attributes).
- **Resource** — `owner: User` — the resource's root owner. Owners
  always retain access; cascading revocation never affects an owner's
  own permission to read their own resource.

## Context attributes (for `read`)

| Attribute            | Meaning                                          |
|----------------------|--------------------------------------------------|
| `now`                | Current request timestamp (informational).       |
| `accessAuthorized`   | Host-attested: a full, unbroken grant chain     |
|                      | from `resource.owner` to `principal` exists.     |
| `revocationDetected` | Host-attested: at least one link in the chain   |
|                      | has been revoked.                                |

## Access rule (single action: `read`)

A `read` is permitted iff **either** of:

1. `principal == resource.owner` (owner bypass — owners always read
   their own resources, regardless of the attestation flags).
2. `accessAuthorized && !revocationDetected` (a non-owner principal
   has a valid, non-cascade-invalidated derived permission).

Otherwise, `read` is denied.

## Notes

- The two attestations are **independent boolean flags**, even though
  they are semantically related. The host computes them separately, so
  it is possible (though unusual) for both to be true; the policy must
  treat `revocationDetected == true` as overriding `accessAuthorized`.
- The owner bypass must NOT be conditioned on
  `revocationDetected`. An owner cannot have their own grant chain
  revoked — they are the root. Conditioning the owner branch on
  attestation flags is a common bug.
- Common failure modes:
  - (a) Forgetting the owner bypass and gating all reads on
    `accessAuthorized`, which fails the owner-only floor.
  - (b) Forgetting to negate `revocationDetected`, which permits
    cascade-revoked derived users.
  - (c) Conditioning the owner branch on `accessAuthorized`, which
    breaks owner-only floors when the host (correctly) reports
    `accessAuthorized == false` for owners (since owners have no chain).
