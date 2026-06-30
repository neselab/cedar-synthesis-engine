---
pattern: context-scoped admin
difficulty: medium
features:
  - set membership
  - role-vs-capability separation
  - tenant scoping
domain: multi-tenant SaaS / platform
synthesis_difficulty: 2
---

# Context-Scoped Admin — Policy Specification

## Context

This policy governs administrative authority on a multi-tenant
platform where "admin" is NOT a global role. Each `User` carries a
free-form `role` string AND an `adminOf: Set<Tenant>` set listing the
specific tenants in which they may act as an administrator.

Every `Resource` belongs to exactly one `Tenant` (`resource.tenant`).
Three actions are governed: `view`, `modify`, and `delete`.

The fundamental safety property: **admin powers do not cross tenant
boundaries.** A user with `role == "admin"` whose `adminOf` set does
NOT include a particular tenant has no authority over that tenant's
resources, even though the role string suggests otherwise. The role
string is metadata; `adminOf` is the source of truth for capability.

## Requirements

### 1. View — Scoped to Admin Tenants
- A User may `view` a Resource when the resource's tenant appears in
  the user's `adminOf` set:
  `principal.adminOf.contains(resource.tenant)`.
- No other gating: any user (regardless of role string) whose
  `adminOf` includes the resource's tenant may view.

### 2. Modify — Scoped to Admin Tenants
- A User may `modify` a Resource under exactly the same condition:
  `principal.adminOf.contains(resource.tenant)`.

### 3. Delete — Scoped to Admin Tenants
- A User may `delete` a Resource under exactly the same condition:
  `principal.adminOf.contains(resource.tenant)`.

### 4. Cross-Tenant Admin — Always Forbidden
- A User whose `adminOf` does NOT contain the resource's tenant may
  not `view`, `modify`, or `delete` that resource, regardless of the
  user's `role` string. In particular, `role == "admin"` confers no
  cross-tenant authority on its own.

## Notes
- The `role` string is informational. Do not gate any of the three
  actions on `principal.role == "admin"` — that is the trap. A user
  flagged as "admin" but with `adminOf == []` (the empty set) is, by
  this policy, an administrator of nothing.
- The set-containment check `principal.adminOf.contains(resource.tenant)`
  is the canonical scoping primitive. Cedar's symbolic compiler
  reasons cleanly about set membership of entity references.
- A user can be `adminOf` zero, one, or many tenants. The policy
  composes naturally: the more tenants in `adminOf`, the more
  resources the user may act upon, but each resource is checked
  independently against the set.
- Cedar denies by default. The three permit rules above are
  sufficient — no explicit forbid is required to block the
  cross-tenant case, because there is no permit that matches it.
