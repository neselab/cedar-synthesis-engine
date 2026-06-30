---
pattern: tacit domain convention (standard RBAC)
difficulty: hard (planning)
features:
  - role hierarchy inference
  - domain shorthand
  - implicit conventions
domain: content management system
synthesis_difficulty: 3
---

# Standard RBAC for a Content Management System

## Context

Implement standard RBAC for a content management system. Roles are
`viewer`, `editor`, and `admin`. Apply the usual hierarchy.

## Entities

- **User** -- principal. Has a `role` string: `"viewer"`, `"editor"`,
  or `"admin"`.
- **Article** -- resource.

## Actions

- **view** -- read an article.
- **edit** -- modify an article.
- **delete** -- delete an article.

## Quick reference

| Action  | Minimum role |
|---------|--------------|
| view    | viewer       |
| edit    | editor       |
| delete  | admin        |

## Out of scope

- No per-article ownership.
- No global forbids.
- No temporal constraints.
- No entity hierarchies (users in groups, etc.).

## Notes for the planner

This spec deliberately uses domain shorthand. The phrases "standard RBAC"
and "the usual hierarchy" are tacit conventions that you must unpack:

- **Default deny.** Only the listed permits apply; nothing else.
- **Role inheritance** (the "usual hierarchy"): `admin` >= `editor` >=
  `viewer`. A higher role inherits every permission of every lower role,
  in addition to its own. Concretely:
  - A `viewer` may `view`.
  - An `editor` may `view` AND `edit`.
  - An `admin` may `view`, `edit`, AND `delete`.
- The "minimum role" column in the quick-reference table is the FLOOR of
  who is allowed; anyone at or above that role in the hierarchy is also
  allowed.

### Liveness

Each of the three actions must permit at least one request.
