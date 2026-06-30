---
pattern: union semantics adversarial (cross-product trap)
difficulty: hard
features:
  - permit-union semantics
  - coupled (attribute, attribute) conditions
  - adversarial cross-product encoding trap
domain: access control / general
synthesis_difficulty: 4
---

# Union Semantics Adversarial — Policy Specification

## Context

A system has `User` principals with two boolean group memberships
(`groupA`, `groupB`) and `Resource` objects with a `category` String
that is either `"alpha"` or `"beta"`. The single action `access`
governs whether a user may access a resource.

This scenario is **adversarial**: it tests whether the synthesizer
correctly couples each group to its corresponding category, or whether
it falls into the naive cross-product trap that Cedar's permit-union
semantics make easy to write.

## Requirements

### 1. groupA may access alpha
A User with `principal.groupA == true` may `access` a Resource
with `resource.category == "alpha"`.

### 2. groupB may access beta
A User with `principal.groupB == true` may `access` a Resource
with `resource.category == "beta"`.

### 3. No cross-group access
A user who is **only** in groupA must NOT access beta resources.
A user who is **only** in groupB must NOT access alpha resources.

### 4. Dual-group users
A user in BOTH groupA and groupB inherits both grants: they may
access alpha resources (via groupA) AND beta resources (via groupB).
They must NOT, however, gain any access beyond the union of the two
individual grants.

### 5. Default deny
A user with neither `groupA` nor `groupB` may not access any
resource. A resource whose `category` is neither `"alpha"` nor
`"beta"` may not be accessed by anyone.

## The Trap

The natural-language requirements above can be summarized as
"users in either group can access either category" — which encourages
the WRONG encoding:

```cedar
permit (principal is User, action == Action::"access", resource is Resource)
when {
    (principal.groupA || principal.groupB)
    && (resource.category == "alpha" || resource.category == "beta")
};
```

This permits a groupA-only user to access a beta resource, violating
requirement 3. Cedar's permit-union semantics mean two individually
sound permits — `permit when groupA && alpha` and
`permit when groupB && beta` — are also acceptable; what is NOT
acceptable is collapsing them into a single cross-product permit.

The CORRECT encoding couples each group to its category:

```cedar
permit (principal is User, action == Action::"access", resource is Resource)
when {
    (principal.groupA && resource.category == "alpha")
    || (principal.groupB && resource.category == "beta")
};
```

Equivalently, two separate permits (one per (group, category) pair)
also satisfy the spec because permits union safely when each is
individually correct.
