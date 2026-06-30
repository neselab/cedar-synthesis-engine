---
pattern: multi-tenant isolation at scale (100 distinct tenants)
difficulty: hard (scale, not semantics)
features:
  - 100 distinct tenant identifiers verified individually
  - Tenant-ID equality enforcement (cross-tenant denied by default)
  - 1 ceiling + 100 per-tenant floors + 1 liveness = 102 checks
domain: multi-tenant SaaS, meta-harness scale test
synthesis_difficulty: 3
---

# Hundred-Tenant Isolation — Multi-Tenant SaaS Policy

## Context

This policy governs access control for a multi-tenant SaaS platform.
Every `User` carries a `tenantId: String` attribute identifying their
home tenant. Every `Resource` carries a `tenantId: String` attribute
identifying the tenant that owns it. There is exactly one action,
`access`, which applies to any `(User, Resource)` pair.

The platform serves 100 distinct tenants, with identifiers
`"tenant_0"`, `"tenant_1"`, ..., `"tenant_99"`. There are no
super-admins, no cross-tenant escape hatches, no support-session
overrides. Tenant isolation is absolute.

## Requirements

### Same-Tenant Access (Permit)

A `User` may `access` a `Resource` if and only if their `tenantId`
attributes are equal: `principal.tenantId == resource.tenantId`. No
other conditions apply.

### Cross-Tenant Access — Always Forbidden

A `User` may never `access` a `Resource` whose `tenantId` differs from
their own, regardless of which two tenants are involved. There is no
allowlist of "trusted" cross-tenant pairs and no global-support
override. Cedar's default-deny suffices for cross-tenant requests; an
explicit `forbid` is acceptable but not required.

## Notes

- The policy itself is trivial in Cedar — a single permit rule with a
  string-equality condition expresses the entire requirement.
- The challenge for the harness is **scale of verification**: the
  verification plan enumerates 100 distinct floor checks, one per
  tenant, each asserting "a user from `tenant_X` MUST be permitted to
  `access` a resource from `tenant_X`." A correct policy passes all
  100 simultaneously; a buggy policy that hardcodes a wrong tenant or
  uses substring matching fails on a specific subset.
- Common pitfalls:
  - Hardcoding a particular tenant ID instead of comparing the two
    attributes.
  - Using `like` or substring matching, which would over-permit
    (e.g., `tenant_1` would match `tenant_10`, `tenant_11`, ...).
  - Forgetting the `is User` / `is Resource` type guards (not
    strictly required since the action only applies to those types,
    but defensive).
- Liveness: at least one `(principal, resource)` pair must be
  permitted; the single liveness check ensures the policy is not
  vacuously a `forbid-everything`.
