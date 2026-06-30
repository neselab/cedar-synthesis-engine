---
pattern: overlapping permission scopes (editor role vs ownership)
difficulty: hard
features:
  - role-based access alongside ownership
  - disjunctive permission (OR-shaped)
  - ambiguous English-language specification
domain: document collaboration
synthesis_difficulty: 3
---

# Specification Ambiguity -- Editors and Owners

## Context

This scenario models a document collaboration platform where two
permission paths grant edit access on documents:

1. A **role-based** path: users carrying the `editor` role have broad
   edit rights across the document corpus.
2. An **ownership-based** path: any user may edit the documents they
   own.

The specification is intentionally written in compact natural-language
form that admits two readings; the intended reading is the more permissive
one (logical OR), and a candidate that picks the more restrictive
reading (logical AND) will be discriminated against by a specific
counterexample floor.

## Entities

- `User` with attribute `role: String` (e.g. `"editor"`, `"viewer"`,
  `"contributor"`).
- `Document` with attribute `owner: User`.

## Action

- **edit** -- modify document contents.

## Requirements

The English specification reads:

> "Editors can edit any document. Owners can edit their own documents."

The intended interpretation is **disjunctive**: a user is permitted to
edit a document when EITHER of the following holds:

1. `principal.role == "editor"` (regardless of who owns the document), OR
2. `principal == resource.owner` (regardless of role).

A user who is an editor but does not own the document MUST be permitted
to edit it -- this is the discriminating case that rules out the
incorrect AND-reading. Likewise, a user who owns the document but does
not have the editor role MUST be permitted to edit it.

### Floors

- **Floor A (editor, non-owner):** A user with `role == "editor"` who
  does NOT own the document MUST be permitted to edit it. This is the
  counterexample that rules out the over-restrictive AND interpretation.
- **Floor B (owner, non-editor):** A user who owns the document but has
  `role != "editor"` MUST be permitted to edit it.
- **Floor C (editor, owner):** A user who is both an editor and the
  document's owner MUST be permitted to edit it (the trivial overlap
  case).

### Ceiling

`edit` is permitted only when `principal.role == "editor"` OR
`principal == resource.owner`. No other path grants edit.

### Liveness

The `edit` action must permit at least one request.

## Out of scope

- No other actions (no `view`, `delete`, `share`).
- No organization / tenant isolation.
- No temporal or contextual constraints.
- No global forbids.
