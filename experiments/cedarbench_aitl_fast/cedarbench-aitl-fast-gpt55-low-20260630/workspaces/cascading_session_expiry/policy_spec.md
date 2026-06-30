---
pattern: cascading session expiry (min of two timestamps)
difficulty: medium
features:
  - datetime comparison
  - effective expiry as min of parent + self
  - entity in context
  - if-then-else equivalence with conjunction
domain: identity / session management
synthesis_difficulty: 3
---

# Cascading Session Expiry -- Policy Specification

## Context

Modern authentication systems often use a hierarchical session model:
an umbrella "parent" session (e.g. an SSO refresh token) issues
shorter-lived "child" sessions (e.g. per-application access tokens).
The child session is usable iff BOTH the parent and the child are
themselves still valid at request time. Equivalently, the child's
*effective* expiry is the EARLIER (the minimum) of the two timestamps.

Cedar has no built-in `min` operator. There are two equivalent ways to
encode "now must be before the minimum of two expiries":

1. **Conjunction (idiomatic, simpler):**
   ```
   context.now < context.session.parentExpiresAt
   && context.now < context.session.selfExpiresAt
   ```
2. **If-then-else (explicit min):**
   ```
   context.now < (if context.session.parentExpiresAt
                     < context.session.selfExpiresAt
                  then context.session.parentExpiresAt
                  else context.session.selfExpiresAt)
   ```

Both formulations are logically equivalent. This scenario uses the
**conjunctive form** in its references because it is the idiomatic Cedar
encoding and is what a synthesizer should produce.

Entities: `User`, `Session` (with `parentExpiresAt: datetime` and
`selfExpiresAt: datetime`), and `Resource`. The request context carries
`now: datetime` and `session: Session` (the session record looked up
and attached by the host application).

One action: `useSession` (the user attempts to use their session to
access a resource).

## Requirements

### 1. useSession Permitted Only Before Effective Expiry (Permit)

A User may perform the `useSession` action on a Resource if and only
if the current time `context.now` is strictly before BOTH expiries
of the session attached in `context.session`:

- `context.now < context.session.parentExpiresAt`, AND
- `context.now < context.session.selfExpiresAt`.

Equivalently: `context.now < min(parentExpiresAt, selfExpiresAt)`.

### 2. useSession Forbidden When Either Expiry Has Passed (Deny by Default)

If either the parent or the self expiry has been reached
(`context.now >= context.session.parentExpiresAt` OR
`context.now >= context.session.selfExpiresAt`), the action MUST be
denied. Cedar's deny-by-default semantics make this an implicit
consequence of (1).

## Notes

- The `now` and the two expiries are all `datetime` values in UTC.
- Comparisons use Cedar's native `<` operator on `datetime`. Both
  strict (`<`) and non-strict (`<=`) variants are reasonable; this
  scenario adopts the strict-less-than convention (a session expires
  at the instant the timestamp is reached).
- The host application is responsible for looking up the session
  record and attaching it as `context.session`.
- The "entity in context" pattern is supported by Cedar: the schema
  declares `session: Session` directly in the context shape, and the
  policy reads attributes via `context.session.parentExpiresAt`.
- A synthesizer that uses the if-then-else form is also correct
  because it is logically equivalent to the conjunction. The
  reference encodes the conjunction, and the ceiling/floor checks
  pass for either encoding.
