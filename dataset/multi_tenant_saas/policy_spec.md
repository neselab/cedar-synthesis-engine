# Multi-Tenant SaaS — Policy Specification

## Context

This policy governs access control for a multi-tenant SaaS platform.
Every User belongs to a home Tenant (`user.tenant`), and every Resource
also belongs to a Tenant (`resource.tenant`). The fundamental
requirement is **tenant isolation**: a user should only be able to see
or modify resources belonging to their own tenant. The single narrow
exception is a global-support cross-tenant *read* path, subject to
tight preconditions.

Three actions: `readResource`, `writeResource`, `deleteResource`. All
three take a context with `supportSessionActive: Bool` and `ticketId:
String`.

## Requirements

### 1. Tenant-Owned Same-Tenant Access (Permit)
- A User may perform any action on a Resource when their `tenant`
  matches the Resource's `tenant`: `principal.tenant == resource.tenant`.
- No additional conditions apply to same-tenant access. The context
  fields (supportSessionActive, ticketId) do not need to be set for
  same-tenant requests — they are used only for the cross-tenant path.
- Specifically: permit `readResource`, `writeResource`, `deleteResource`
  when `principal.tenant == resource.tenant`.

### 2. Global Support Cross-Tenant Read (Permit — Narrow)
- A User who is on the global support team (`principal.isGlobalSupport
  == true`) may `readResource` a Resource belonging to any tenant,
  provided ALL of:
  - An active support session is in progress: `context.supportSessionActive
    == true`, AND
  - A non-empty ticket ID is attached to the request: `context.ticketId
    != ""`.
- This path applies ONLY to the `readResource` action. Global support
  users have no cross-tenant write or delete capability under any
  circumstance.

### 3. Cross-Tenant Write and Delete — Always Forbidden
- A User may never `writeResource` or `deleteResource` on a Resource
  from a different tenant, regardless of global-support status,
  support-session state, or ticket reference. Cross-tenant mutation is
  strictly prohibited.

## Notes
- Tenant isolation is the fundamental SaaS safety property. The
  global-support cross-tenant read path is a narrow, audited escape
  hatch — the conditions (global support role, active session, ticket
  reference) must ALL hold together, and it applies only to read.
- The permit rules in §1 and §2 grant access. Cedar denies by default,
  so there is no need for an explicit forbid on cross-tenant
  read/write/delete — the absence of a matching permit is sufficient.
  However, a defensive `forbid` on cross-tenant write/delete is also
  acceptable and gives stronger signal that those actions are
  intentionally blocked.
- The context fields `supportSessionActive` and `ticketId` exist on all
  three actions (per the schema), but they only matter for the
  global-support read path. Same-tenant access ignores them.
- Common pitfalls: forgetting to check the support-session state (just
  checking `isGlobalSupport` is insufficient), authorizing
  cross-tenant write for global support, or forgetting the ticketId
  attestation.
