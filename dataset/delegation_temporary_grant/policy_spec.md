---
pattern: delegation (ephemeral grant)
difficulty: medium
features:
  - optional context attribute (`has` guarding)
  - datetime comparison on nested record attribute
  - fallback access path (owner vs grantee)
  - per-action scoping on the same grant
domain: engineering / SRE
---

# Delegation with Temporary Grant — Policy Specification

## Context

This policy implements time-bounded access delegation. A Resource has
an `owner` who may always act on it. The owner can also issue temporary
grants to other users, authorizing them to perform a specific action
(read or write) on the resource until a pinned expiry datetime.

In production, the grant database is managed by the host application.
When a request comes in, the host looks up "is there an active,
unexpired grant from this user on this resource for this action?" and,
if found, attaches the grant to the request context as the optional
`activeGrant` attribute. The policy verifies the grant's claims
against the request.

Principal is `User`; resource is `Resource`. Four actions: `read`,
`write`, `createGrant`, `revokeGrant`.

## Requirements

### 1. Owner Baseline Access
- The resource's owner may always `read`, `write`, `createGrant`, and
  `revokeGrant`. No grant lookup needed.
- Concretely: for each of the four actions, permit when
  `principal == resource.owner`.

### 2. Grant-Based Read
- A non-owner User may `read` the Resource when ALL of the following
  hold:
  - The request's context includes an `activeGrant` attribute
    (`context has activeGrant`), AND
  - The grant's `grantee` is the principal: `context.activeGrant.grantee
    == principal`, AND
  - The grant's `allowedAction` is `"read"`, AND
  - The grant has not expired: `context.activeGrant.expiresAt >
    context.now.datetime`.

### 3. Grant-Based Write
- A non-owner User may `write` the Resource under the same conditions
  as §2, but with `allowedAction == "write"`. A "read" grant does NOT
  authorize writing, and vice versa.

### 4. Grant Management (Owner Only)
- Only the owner may `createGrant` or `revokeGrant`. Grantees themselves
  have no authority to create grants for other users, even if they have
  an active grant of their own.

## Notes
- The `activeGrant` attribute is **optional** in the schema (declared
  with `?`). Per Cedar's type-checker, every read of
  `context.activeGrant.X` must be guarded by `context has activeGrant`
  in the same conjunct. A naive policy that reads `context.activeGrant.grantee`
  without the `has` guard will fail Cedar validation.
- The grant's `expiresAt` check uses `>` (strict inequality): a grant
  that expires exactly at `context.now.datetime` is no longer valid.
- The policy intentionally uses separate permits for read and write
  grants because a single grant authorizes only one action. Attempting
  to collapse the two into one permit with a combined action check
  (`action in [read, write]`) breaks the action-scope semantics.
- Common failure modes: (a) forgetting the `has` guard on the optional
  attribute, (b) using `==` instead of `>` on the expiry check
  (permitting the exact-expiry boundary case), (c) missing the
  `allowedAction` string match and thus allowing cross-action use of
  a single grant.
