---
pattern: self-referential corner case / §8.8 regression test
difficulty: hard (for bound consistency)
features:
  - owner baseline permit
  - global blocking forbid (Set<User> containment)
  - self-blocking corner case
domain: social platforms with "quiet mode"
---

# Self-Reference Corner Case — Policy Specification

## Context

This policy governs access to Posts on a social platform. The core
rules are simple on their surface:

- **Authors can always read their own posts.**
- **Blocked users cannot read posts by the person who blocked them.**

The subtlety is that the platform supports "quiet mode" — a user can
add themselves to their own `blocked` set to stop seeing their own
posts in their feed. This is a real feature on some messaging
platforms. The interaction between the owner-can-read rule and the
blocked-users-cannot-read rule creates a corner case: what happens
when the author has self-blocked?

The intended semantics: **the blocking forbid wins**. A user who has
quieted themselves cannot read their own posts. This is what the
author opted into by self-blocking.

## Requirements

### 1. Author Read Access
- The author of a Post may `readPost` their own post, subject to the
  global blocking forbid in §3.
- Concretely: permit `readPost` when `principal == resource.author`.

### 2. Public Read Access
- Any User may `readPost` any Post authored by someone who has not
  blocked them, subject to the global blocking forbid in §3.
- Concretely: permit `readPost` for `principal is User`
  unconditionally (any User can read any Post, filtered by the
  forbid).

### 3. Mutual Blocking (Forbid)
- **Forbid** `readPost` when EITHER:
  - the post's author has blocked the principal
    (`principal in resource.author.blocked`), OR
  - the principal has blocked the post's author
    (`resource.author in principal.blocked`).
- This forbid applies to EVERY principal, including the author
  themselves. A self-blocked author is blocked from reading their
  own posts — this is intentional and is the "quiet mode" semantics.

## Notes
- This spec is deliberately constructed to exercise the §8.8
  floor-bound consistency rule. A naive Phase 1 planner would write:
  - Floor: "author MUST be permitted to read their own post"
    (`permit when principal == resource.author`)
  - Ceiling: "reader must not be blocked"
    (`permit unless blocking conditions`)
  These contradict in the self-block corner case. Per §8.8, the
  correct floor must include the blocking exclusion:
  `permit when principal == resource.author AND NOT (principal in
  resource.author.blocked) AND NOT (resource.author in principal.blocked)`
  — i.e., the floor must explicitly acknowledge that self-blocked
  authors are not guaranteed read access.
- The interaction of the `principal` self-blocking and
  `resource.author` self-blocking is the same condition because of
  the `principal == resource.author` premise — both reduce to "is the
  principal in their own blocked set?".
- Cedar's `Set<User>.contains()` / `in` operator handles self-reference
  without any special-case handling; no type error occurs.
