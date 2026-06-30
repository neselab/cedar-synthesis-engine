---
pattern: default scope mismatch (tenant default vs user-level admin override)
difficulty: medium
features:
  - cross-tenant unconditional forbid
  - tenant-level boolean default flag
  - user-level role override of tenant default
  - asymmetric read/write authorization
domain: multi-tenant SaaS
synthesis_difficulty: 3
---

# Default Scope Mismatch — Policy Specification

## Context

This policy governs a multi-tenant document store where access defaults
are configured at the **tenant scope** (an org-wide kill switch) but can
be **overridden at the user scope** by an administrator role. The
fundamental tension: when scopes disagree, who wins?

The answer here: **cross-tenant** is an unconditional gate (no scope
can override it), but **tenant-default-deny** is overridable by a
user-scope admin role. Write operations are additionally restricted to
the admin role even when default-deny is off.

## Entities

- `User` with attributes:
  - `role: String` — one of `"member"` or `"admin"` for our purposes.
  - `tenant: Tenant` — the user's home tenant.
- `Tenant` with attributes:
  - `defaultDeny: Bool` — when `true`, the tenant's documents are
    blocked by default, except for tenant admins.
- `Document` with attributes:
  - `tenant: Tenant` — the document's owning tenant.

## Actions

- `read` on a `Document`.
- `write` on a `Document`.

## Requirements

### 1. Cross-tenant is unconditionally forbidden
- If `principal.tenant != resource.tenant`, deny both `read` and
  `write`. No role, context, or tenant flag may override this. This is
  the tenant-isolation guarantee.

### 2. Tenant default-deny gates same-tenant access
- If `principal.tenant == resource.tenant` AND
  `principal.tenant.defaultDeny == true`:
  - Same-tenant **non-admin members are forbidden** from `read` and
    `write`.
  - Same-tenant **admins** (`principal.role == "admin"`) are still
    permitted to `read` (and to `write`, see §3). The admin role is the
    user-scope override of the tenant-scope default.

### 3. Same-tenant write requires admin
- Independent of the `defaultDeny` flag, `write` on a `Document` is
  permitted only when `principal.tenant == resource.tenant` AND
  `principal.role == "admin"`. Members may not write under any
  circumstance.

### 4. Same-tenant read with default-allow
- When `principal.tenant == resource.tenant` AND
  `principal.tenant.defaultDeny == false`, **any** user in the same
  tenant (member or admin) may `read` the document.

## Notes

- The default-deny flag at the tenant scope is the global setting; the
  admin role at the user scope is the per-user override. Encoding the
  cross-tenant gate as an *unconditional* forbid is what makes this
  scenario distinct from one where the admin role can also override
  cross-tenant — admins are NOT a superuser; they are a per-tenant
  authority.
- Common pitfall: writing the cross-tenant forbid as conditional on
  role (e.g. `unless principal.role == "admin"`) would let an admin in
  tenant A read documents in tenant B — a serious tenant-isolation
  bug. The cross-tenant forbid must be unconditional.
- Another common pitfall: forgetting that `write` is admin-only inside
  the same tenant, regardless of the `defaultDeny` flag. A
  default-allow tenant still does not give members write access.
