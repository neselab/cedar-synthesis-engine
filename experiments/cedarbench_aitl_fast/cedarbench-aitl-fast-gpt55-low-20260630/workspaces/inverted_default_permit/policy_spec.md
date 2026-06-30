---
pattern: inverted default-permit with denylist
difficulty: hard
features:
  - permit-by-default semantics
  - explicit denylist via Set membership
  - inversion of Cedar's natural deny-by-default model
domain: public content / publishing
synthesis_difficulty: 3
---

# Inverted Default-Permit (Public Content with Denylist)

## Context

This scenario inverts Cedar's natural deny-by-default model. The resource is
a `PublicArticle` -- a piece of content that is, by editorial intent,
**publicly readable**. Rather than enumerating who *can* read it, the article
maintains a small list of explicitly-banned reader IDs (e.g. abusive users,
sanctioned accounts, jurisdictional blocks).

The pattern tests whether the policy author can correctly translate
"publicly readable except for a denylist" into Cedar without falling back to
a deny-by-default formulation. Cedar permits are unioned, so a broad
permit + narrow forbid (or a single broad permit guarded by a `!contains`)
is the correct shape.

## Entities

- **User** -- principal. Has a string `id` (the user's stable identifier,
  e.g. `"u_42"`).
- **PublicArticle** -- resource. Has a `bannedReaders: Set<String>` of
  user IDs that are explicitly denied read access. The set may be empty
  (no one is banned) or contain any number of IDs.

## Actions

- **read** -- read the article's content.

## Requirements

### Action: read

A User may **read** a PublicArticle when:

- The user's `id` is **NOT** in the article's `bannedReaders` set.

That is the *only* condition. PublicArticles are publicly readable by
default; the only way a read is denied is if the user's id is in the
explicit denylist. There is no group membership, no role check, no
authentication state to inspect -- by design.

### Encoding guidance

Cedar's natural model is deny-by-default plus permits. To encode
"publicly readable except for X," the natural Cedar shape is a single
broad permit:

```
permit (principal is User, action == Action::"read", resource is PublicArticle)
when { !resource.bannedReaders.contains(principal.id) };
```

Any equivalent that yields the same permit set is acceptable (e.g.
unconditional permit + forbid for banned users). What is **not**
acceptable is a permit that requires some additional positive condition
(group membership, allowlist, role) -- that would over-deny the spec.

Floors:
- A user whose `id` is **not** in `bannedReaders` MUST be permitted to read.
- A user whose `id` is **not** in `bannedReaders` AND where `bannedReaders`
  is empty MUST be permitted to read (this is a strictly weaker subcase of
  the above; included to anchor the empty-denylist case explicitly).

### Liveness

The `read` action must permit at least one request -- no global deny.

## Out of scope

- No authentication / "must be logged in" check.
- No role hierarchy, group membership, or organization scoping.
- No time-of-day or rate-limit constraints.
- No write/edit/delete actions; reads only.
- No global forbids beyond what the policy itself encodes.
