---
pattern: dual-owner joint consent
difficulty: hard
features:
  - dual ownership (two owner attributes)
  - order-symmetric consent matching
  - optional record context attributes (has-guards required)
  - duration-based freshness window
domain: finance / shared assets
synthesis_difficulty: 4
---

# Dual-Owner Joint Consent — Policy Specification

## Context

Some assets are co-owned by exactly **two** principals — joint bank
accounts, shared brokerage accounts, jointly-titled property records,
and so on. Read-only access (`view`) follows the usual single-owner
rule: either co-owner may inspect the asset at any time. State-changing
access (`transfer`) requires **fresh signed attestations from BOTH
co-owners**, presented together in the request context.

The two consent attestations are independent records — the request may
present them in either order. The policy must accept both
`(consent1=owner1, consent2=owner2)` and `(consent1=owner2,
consent2=owner1)` and reject any other pairing of signers.

## Entities

- **User** — opaque principal; no attributes.
- **JointAsset** — `owner1: User`, `owner2: User`. Exactly two owners,
  represented as two distinct entity-typed attributes (not a set).

## Actions and context

### `view`

Either co-owner may view at any time. No consent is required.

Context:

| Attribute | Type | Notes |
|-----------|------|-------|
| `now` | `datetime` | Current request time. Not consulted by `view`. |

### `transfer`

Both co-owners must have signed a consent attestation within the last
24 hours. The two consents are presented as **optional** record-typed
context attributes:

| Attribute | Type | Notes |
|-----------|------|-------|
| `now` | `datetime` | Current request time. |
| `consent1?` | `{ signer: User, signedAt: datetime }` | Optional record. |
| `consent2?` | `{ signer: User, signedAt: datetime }` | Optional record. |

Because `consent1` and `consent2` are optional, every read of their
fields must be guarded by `context has consentN` in the same
conjunction (§8.3 — Cedar's type-checker does not propagate negation
or optionality through nested record reads).

## Access rules

### 1. View

Permit when `principal == resource.owner1 || principal == resource.owner2`.

### 2. Transfer

Permit when **all** of the following hold:

1. Both `consent1` and `consent2` are present in the context.
2. The two signers cover both owners — accept either ordering:
   - `consent1.signer == owner1 && consent2.signer == owner2`, OR
   - `consent1.signer == owner2 && consent2.signer == owner1`.
3. Both consents were signed within the last 24 hours:
   - `now.durationSince(consent1.signedAt) <= 24h` AND
   - `now.durationSince(consent2.signedAt) <= 24h`.
4. Both `signedAt` timestamps are not in the future — i.e.
   `durationSince(...) >= 0h` for both. (Defense against clock-skew
   attacks where a forged consent is post-dated.)

The `principal` of the transfer request is **not** required to be one
of the owners. A trusted notary or escrow service may submit the
transfer with the two signed consents — the consents themselves are
the authorization.

## Notes

- **Order-symmetry trap**: a naive policy hard-codes one order
  (e.g. `consent1.signer == owner1 && consent2.signer == owner2`),
  which violates the ceiling because it permits the swapped form too —
  no, it actually under-permits. The hand-crafted floor uses canonical
  order, so a policy that hard-codes only one direction will pass the
  floor but fail the ceiling on a model-generated swap. Conversely a
  policy that conjoins both directions instead of disjoining them is
  unsatisfiable and fails liveness.

- **Single-consent shortcut**: a policy that requires only one fresh
  consent (rather than both) over-permits and fails the ceiling on
  requests where one of the two consents is missing or stale.

- **Freshness-asymmetry trap**: a policy that checks freshness on
  `consent1` but forgets `consent2` (or vice versa) over-permits when
  one consent is stale and fails the ceiling.

- **Optional-attr trap**: a policy that reads `context.consent1.signer`
  without first checking `context has consent1` will be rejected by
  `cedar validate` (§8.3).
