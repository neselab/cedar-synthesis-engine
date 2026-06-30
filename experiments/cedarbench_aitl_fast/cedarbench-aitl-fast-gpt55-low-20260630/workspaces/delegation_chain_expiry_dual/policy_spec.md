---
pattern: delegation chain (dual-hop time-bounded)
difficulty: hard
features:
  - two optional context attributes (`has` guarding required on both)
  - nested datetime windows with intersection semantics
  - chain-of-trust validation (delegator continuity check)
  - owner fallback path
domain: enterprise / authorization
synthesis_difficulty: 4
---

# Delegation Chain with Dual Expiry — Policy Specification

## Context

This policy implements a two-hop time-bounded delegation chain. The
canonical scenario: User A (the resource owner) delegates an action to
User B at time T1 with expiry T1 + 30 days. User B then delegates the
same action onward to User C at time T2 (where T2 may be later than T1)
with expiry T2 + 7 days. User C may act on the resource only during the
intersection of both delegation windows.

In production, the host application maintains the delegation database
and walks the chain when a request comes in, attaching the relevant
links to the request context as optional `firstGrant` and `secondGrant`
attributes. The policy verifies the chain's claims against the request:
the first grant's grantee must be the second grant's delegator, the
second grant's grantee must be the requesting principal, and BOTH
windows must be currently open.

Principal is `User`; resource is `Resource`. Two actions: `read`,
`write`.

## Requirements

### 1. Owner Baseline Access
- The resource's owner may always `read` and `write` the resource
  without any delegation lookup.
- Concretely: for each action, permit when `principal == resource.owner`.

### 2. Single-Hop Delegation
- A non-owner User may act on the Resource when ALL of the following
  hold (single-hop case — only the first grant is present):
  - `context has firstGrant`, AND
  - `context.firstGrant.delegatee == principal`, AND
  - `context.firstGrant.grantedAt <= context.now`, AND
  - `context.firstGrant.expiresAt >= context.now`.

### 3. Two-Hop Delegation Chain
- A non-owner User may act on the Resource when ALL of the following
  hold (chain case — both grants are present):
  - `context has firstGrant`, AND
  - `context has secondGrant`, AND
  - `context.firstGrant.delegatee == context.secondGrant.delegator`
    (chain-of-trust continuity), AND
  - `context.secondGrant.delegatee == principal`, AND
  - `context.firstGrant.grantedAt <= context.now`, AND
  - `context.firstGrant.expiresAt >= context.now`, AND
  - `context.secondGrant.grantedAt <= context.now`, AND
  - `context.secondGrant.expiresAt >= context.now`.

The two-hop authorization is effective ONLY during the intersection of
both delegation windows. If either window has not yet opened or has
already closed, the chain does not authorize access.

## Notes
- Both `firstGrant` and `secondGrant` are **optional** in the schema
  (declared with `?`). Per Cedar's type-checker, every read of
  `context.firstGrant.X` must be guarded by `context has firstGrant`
  in the same conjunct (and similarly for `secondGrant`). A naive
  policy that reads either grant's attributes without a `has` guard
  will fail Cedar validation. This is the §8.3 negated-`has` trap.
- The temporal checks use `<=` and `>=` (inclusive boundaries on both
  sides of the window).
- The chain-of-trust check is essential. Without
  `firstGrant.delegatee == secondGrant.delegator`, an attacker who
  obtains any first-hop grant could fabricate a second-hop grant
  pointing to themselves and bypass the policy.
- Common failure modes: (a) missing `has` guard on either grant,
  (b) omitting the chain-continuity check, (c) using `==` instead
  of `>=`/`<=` on either window, (d) collapsing single-hop and
  two-hop into one permit and losing the continuity requirement.
