---
pattern: whitelist AND blacklist (positive + negative set membership)
difficulty: medium
features:
  - Set<Entity> attributes on resource (per-endpoint allowlist + denylist)
  - positive set membership via .contains()
  - negated set membership via !...contains()
  - boolean context flag conjunction
domain: API gateway / access control
synthesis_difficulty: 2
---

# Whitelist AND Blacklist — Policy Specification

## Context

A controlled API gateway. Each `Endpoint` carries its own per-endpoint
allowlist (`whitelistedCallers`) and denylist (`blacklistedCallers`) of
`Caller` entities. A request also carries a runtime `trustedSource`
boolean in context (e.g. set true by an upstream attestation step).

This scenario exercises the conjunction of POSITIVE set membership
(allowlist) AND NEGATIVE set membership (denylist) on the same resource —
the classic "allowlist with explicit overrides" pattern.

Note: the denylist is encoded as a per-resource attribute set, NOT as a
role / principal-group. §8.6 (role-intersection trap) does not apply here
because there is no role-keyed forbid — we use attribute-based negation
on the resource, which is sound.

## Requirements

### 1. Invoke — Allowlisted, Not Denylisted, Trusted Source

A `Caller` may `invoke` an `Endpoint` when ALL of:
- The caller is in the endpoint's `whitelistedCallers` set
  (`resource.whitelistedCallers.contains(principal)`), AND
- The caller is NOT in the endpoint's `blacklistedCallers` set
  (`!resource.blacklistedCallers.contains(principal)`), AND
- The request's `context.trustedSource` is `true`.

The denylist takes precedence over the allowlist: a caller present in
both is denied. The trusted-source flag must also be set.

### 2. Default Deny
All other requests are denied.
