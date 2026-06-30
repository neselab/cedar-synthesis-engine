---
pattern: shared inbox delegation
difficulty: medium
features:
  - Set.contains() membership checks
  - three-tier role hierarchy (owner > delegate > member)
  - per-action role gating
domain: enterprise email
synthesis_difficulty: 2
---

# Shared Inbox Delegation -- Policy Specification

## Context

This policy models a shared mailbox system typical of enterprise email
(e.g. "support@company.com", "billing@company.com"). A Mailbox has a
single owner, a set of delegates who can act on behalf of the mailbox,
and a set of members who have read-only access. Four actions are
available: `readMail`, `sendAs`, `manageFolders`, and `grantAccess`.

Membership is tracked via `Set<User>` attributes on the Mailbox entity.
The policy uses `.contains(principal)` checks rather than Cedar entity
group membership (`in`) because the latter blocks symcc liveness
verification.

## Requirements

### 1. readMail -- Owner, Delegates, or Members

A User may `readMail` on a Mailbox when ANY of the following hold:
- The User is the mailbox owner (`principal == resource.owner`), OR
- The User is in the delegates set (`resource.delegates.contains(principal)`), OR
- The User is in the members set (`resource.members.contains(principal)`).

All three tiers have full read access.

### 2. sendAs -- Owner or Delegates Only

A User may `sendAs` (send email appearing to come from the shared
mailbox) when:
- The User is the mailbox owner, OR
- The User is in the delegates set.

Members explicitly cannot send as the mailbox. This is the key
distinction between delegate and member: delegates can represent the
mailbox externally, members cannot.

### 3. manageFolders -- Owner Only

A User may `manageFolders` (create, rename, delete folders within the
mailbox) only when:
- The User is the mailbox owner (`principal == resource.owner`).

Neither delegates nor members may reorganize the mailbox structure.

### 4. grantAccess -- Owner Only

A User may `grantAccess` (add or remove delegates and members) only
when:
- The User is the mailbox owner (`principal == resource.owner`).

Delegates cannot promote other users, even though they have elevated
privileges themselves.

## Notes

- The three-tier hierarchy is strictly: owner > delegate > member.
  Each higher tier inherits all permissions of the lower tiers.
- There are no global forbids in this scenario, so floors do not
  need exclusion clauses (per section 8.8).
- The `Set.contains()` approach is preferred over entity `in` for
  symcc compatibility with liveness checks.
- Common failure mode: collapsing delegates and members into a single
  permit for `sendAs`, which would incorrectly grant members send
  privileges.
