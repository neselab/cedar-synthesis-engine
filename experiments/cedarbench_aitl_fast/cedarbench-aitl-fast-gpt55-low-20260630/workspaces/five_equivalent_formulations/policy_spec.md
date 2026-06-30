---
pattern: semantically-equivalent encodings / canonical-form invariance
difficulty: medium
features:
  - boolean equivalence (de Morgan)
  - if/then/else expression form
  - set-of-one membership form
  - integer comparison vs equality
domain: tiered document access
synthesis_difficulty: 3
---

# Five Equivalent Formulations — Policy Specification

## Context

This scenario tests that the harness accepts ANY semantically-equivalent
encoding of a single access rule. Cedar admits multiple syntactic forms
that compute the same boolean function. The verifier (`cedar symcc`)
operates on Cedar's symbolic semantics — equivalent forms should all
discharge the same ceiling/floor obligations.

Principal is `User` with a `role: String` attribute. Resource is `Doc`
with a `tier: Long` attribute (always one of 1, 2, 3). One action:
`read`.

## Requirements

### Single rule

A User may `read` a Doc when EITHER of the following holds:

- the User's `role` equals `"admin"`, OR
- the Doc's `tier` equals `1`.

That is the entire rule. No other principal/resource pair is permitted
to `read`.

## Equivalent encodings

The following Cedar expressions are all semantically equivalent over
the schema's domain (recall `tier` is always one of `1`, `2`, `3`):

1. `principal.role == "admin" || resource.tier == 1`
2. `principal.role == "admin" || resource.tier <= 1`  (tier is a positive small integer)
3. `(if principal.role == "admin" then true else resource.tier == 1)`
4. `!(principal.role != "admin" && resource.tier != 1)`  (de Morgan)
5. `[principal.role].contains("admin") || resource.tier == 1`  (set-of-one membership)

Any of forms (1)–(5) — or any other expression Cedar's symbolic engine
proves equivalent — is an acceptable implementation. The harness must
not prefer a particular surface syntax.

## Notes

- `tier` is declared as `Long` and is constrained by spec to take
  values 1, 2, 3 only. Encoding (2) relies on this; if the spec ever
  permitted `tier <= 0`, encoding (2) would over-permit and the
  ceiling would catch it. We deliberately keep the "tier in {1,2,3}"
  invariant implicit at the schema level (Cedar `Long` cannot express
  bounded ranges), so a synthesizer that picks form (2) is reasoning
  about the spec's stated invariant, not the schema.
- The ceiling reference uses encoding (1) (the canonical form). The
  three floor references each test a corner of the access rule
  (admin-non-tier-1, non-admin-tier-1, admin-tier-1). The liveness
  check confirms at least one read request is permitted.
