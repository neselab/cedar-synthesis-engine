---
pattern: role-set intersection requirement (must hold ALL of a set)
difficulty: medium
features:
  - Set<String> on both principal and resource
  - ".containsAll()" for set-superset check
  - intersection requirement (every required cert must be held)
  - adversarial — invites the wrong "any of" idiom
domain: industrial / controlled material handling
synthesis_difficulty: 3
---

# Role-Set Intersection Required — Policy Specification

## Context

A controlled-material handling system at an industrial site. Workers
hold a set of safety certifications (`certifications`, e.g. `"hazmat"`,
`"forklift"`, `"cleanroom"`, `"radiation"`, `"confined-space"`).

Materials carry a set of `requiredCerts` indicating every certification
that a worker must hold to physically handle them. For example, a
sealed radioactive sample stored in a cleanroom and moved on a forklift
might require `{"hazmat", "forklift", "cleanroom", "radiation"}` — a
worker holding only `"hazmat"` is NOT qualified.

The interesting semantics: this is an **intersection requirement**, not
the much more common "any of" disjunction. A worker must hold **every**
certification in `resource.requiredCerts`, not merely overlap with it.

The Cedar idiom is `principal.certifications.containsAll(resource.requiredCerts)`
— "the worker's certifications are a superset of the material's
required certs."

## Requirements

### 1. View Access — Open

Any `Worker` may `view` any `Material`. Looking at the catalog entry
for a material (its name, type, location, required certifications) is
not safety-sensitive.

### 2. Handle Access — Full Cert Coverage Required

A `Worker` may `handle` a `Material` only when:
- The worker's `certifications` set contains **every** entry in the
  material's `requiredCerts` set, i.e.
  `principal.certifications.containsAll(resource.requiredCerts)`.

Holding **some** of the required certifications is NOT sufficient. A
worker holding `{"hazmat", "forklift"}` cannot handle a material
requiring `{"hazmat", "forklift", "cleanroom"}` — they lack the
cleanroom certification, and contact would be a safety violation.

A worker holding the empty set `{}` cannot handle any material that has
non-empty `requiredCerts`.

A worker holding a strict superset of the required certs (e.g. they
hold every certification at the site) is permitted, since `containsAll`
is satisfied.

If `requiredCerts` is empty, every worker satisfies `containsAll`
trivially and may handle the material (this matches `containsAll`'s
mathematical definition: every element of the empty set is in any
set).

### 3. Default Deny

All other requests are denied.

## Implementation Note

The natural-but-wrong encoding is `principal.certifications.containsAny(resource.requiredCerts)`,
which permits a worker who holds ANY single required cert. That is the
opposite of the safety requirement and would let an unqualified worker
handle controlled material. Another wrong encoding is to enumerate the
expected certification names with disjunction (`... == "hazmat" || ... == "forklift"`),
which both hard-codes the cert list AND uses OR instead of AND.

The correct encoding uses the set operation `.containsAll(...)`, which
generalizes to any number of required certs without enumeration.
