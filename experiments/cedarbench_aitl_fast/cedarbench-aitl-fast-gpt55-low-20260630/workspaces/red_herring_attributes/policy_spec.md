---
pattern: red herring attributes
difficulty: hard
features:
  - attribute selection focus
  - adversarial irrelevant attributes
  - role string match
  - boolean MFA gate
  - owner equality
domain: adversarial/focus
synthesis_difficulty: 4
---

# Red Herring Attributes -- Policy Specification

## Context

This scenario is an adversarial test of attribute focus. The schema is
deliberately bloated with many descriptive attributes on both the
principal (`User`) and the resource (`Document`). The vast majority of
those attributes are decorative metadata that have NOTHING to do with the
authorization decision. Only three attributes participate in the rule.

The synthesizer's job is to ignore the noise and write a policy that
references only the three relevant attributes. A policy that incorporates
any of the irrelevant attributes (e.g. `timezone`, `accountTier`,
`language`, `category`, `viewCount`) will either be too restrictive
(violating the floor: blocking permitted requests) or too permissive
(violating the ceiling: depending on irrelevant data).

## Attribute Inventory

### `User` -- 10 attributes (3 relevant, 7 red herrings)

Relevant:
- `role: String` -- must be `"reader"` or `"admin"` for view access.
- `mfaVerified: Bool` -- must be `true` for view access.

Red herrings (DO NOT USE in the policy):
- `department: String`
- `timezone: String`
- `language: String`
- `createdAt: datetime`
- `lastLogin: datetime`
- `accountTier: String`
- `referralCode: String`
- `newsletterSubscribed: Bool`

### `Document` -- 8 attributes (1 relevant, 7 red herrings)

Relevant:
- `owner: User` -- the requesting principal must be this user.

Red herrings (DO NOT USE in the policy):
- `title: String`
- `createdAt: datetime`
- `lastModified: datetime`
- `viewCount: Long`
- `category: String`
- `tagCount: Long`
- `publishedDate: datetime`

## Requirements

### View Access (Permit)

A `User` may `view` a `Document` when ALL of the following hold:

1. The user's role is `"reader"` OR `"admin"`:
   `principal.role == "reader" || principal.role == "admin"`.
2. The user's MFA is verified: `principal.mfaVerified == true`.
3. The user is the owner of the document: `principal == resource.owner`.

No other attribute on either entity affects the decision. There are no
explicit forbids; Cedar's default-deny semantics handle every other case.

## Notes

- A user whose `role` is anything other than `"reader"` or `"admin"`
  (e.g. `"viewer"`, `"editor"`, `"guest"`) must NOT be permitted, even
  if they own the document and have MFA verified.
- A user without MFA must NOT be permitted, even if they are the owner
  and have a valid role.
- A user who is not the owner must NOT be permitted, even if they are an
  admin with MFA. Ownership is required for every viewer including admins.
- Common pitfalls: (a) using `accountTier` as a tiered-access proxy --
  it is decorative only; (b) restricting to a `department` -- there is
  no such restriction; (c) gating on `lastLogin` recency -- not in spec;
  (d) gating on document `category` or `viewCount` -- not in spec.
