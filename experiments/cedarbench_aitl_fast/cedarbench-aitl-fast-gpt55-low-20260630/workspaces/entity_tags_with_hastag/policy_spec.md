---
pattern: entity tags with hasTag
difficulty: hard
features:
  - entity tags Set<String> values
  - hasTag operator
  - getTag operator
  - set intersection on tag values
domain: clearance / classified data
synthesis_difficulty: 4
---

# Entity Tags with hasTag/getTag — Policy Specification

## Context

A classified-data access system modeled on the clearance / compartment
structures used in government and defense contexts. Users and Documents
both carry arbitrary **entity tags** (Cedar RFC 0082) — a dynamic
key/value namespace where each key maps to a `Set<String>` of values.

This scenario specifically exercises Cedar's entity tags feature:
- `principal.hasTag("clearance")` — returns `Bool`
- `principal.getTag("clearance")` — returns `Set<String>`
- Tag values are themselves sets (all tags must share a single value type
  in the schema — `Set<String>` here), so set operations like
  `containsAll` / `contains` compose naturally.

This feature is relatively new and most LLMs do not know it exists. The
scenario is intentionally hard: every `getTag` read must be preceded by a
`hasTag` guard, and the negated-`has` trap (§5.4/§8.3) applies to tags
as well as optional attributes.

## Tag vocabulary

Users carry tags for:
- `"clearance"` — values from `{"TS", "S", "C", "U"}` (Top Secret, Secret,
  Confidential, Unclassified). In practice a user holds a single clearance,
  but we model it as a set so `containsAll` can be used uniformly.
- `"compartment"` — values from `{"NOFORN", "SI", ...}` (need-to-know
  compartments).
- `"edit_authorized"` — a boolean-as-string-set; `{"true"}` if the user
  has been separately approved to edit classified material.
- `"role"` — values may include `"declassifier"` (a user permitted to
  downgrade classification).

Documents carry tags for:
- `"required_clearance"` — minimum clearance levels the reader must hold.
  Encoded as a set so dominance checks reduce to `containsAll`.
- `"compartments_required"` — optional. When present, reader must hold
  ALL listed compartments.

## Requirements

### 1. `view` — Clearance + optional compartment check

A User may `view` a Document when ALL of:
- `principal.hasTag("clearance")`, AND
- `resource.hasTag("required_clearance")`, AND
- `principal.getTag("clearance").containsAll(resource.getTag("required_clearance"))`, AND
- IF `resource.hasTag("compartments_required")`, THEN
  `principal.hasTag("compartment")` AND
  `principal.getTag("compartment").containsAll(resource.getTag("compartments_required"))`.

If the document has no `compartments_required` tag, the compartment check
is skipped.

### 2. `edit` — All of view's requirements PLUS edit authorization

A User may `edit` a Document when:
- All of the `view` preconditions hold, AND
- `principal.hasTag("edit_authorized")` AND
- `principal.getTag("edit_authorized").contains("true")`.

### 3. `declassify` — Declassifier role only

A User may `declassify` a Document when:
- `principal.hasTag("role")`, AND
- `principal.getTag("role").contains("declassifier")`.

Declassification is an administrative action; it does NOT require the
clearance/compartment machinery (a declassifier may be authorized to
downgrade documents outside their normal reading scope).

### 4. Default Deny

All other requests are denied. In particular, any request where the user
lacks the prerequisite tag (e.g. no `clearance` tag at all) must be
denied — untagged users have no access.

## Implementation notes for the synthesizer

- `getTag("K")` on an entity that does not have tag `"K"` is a runtime
  error. EVERY `getTag` read MUST be guarded by a `hasTag` check in the
  same `when` clause, combined with `&&` (short-circuit).
- Cedar's type-checker does not propagate negation through `hasTag`, so
  guards must be written in the positive-form pattern:
  `(!resource.hasTag("X") || (resource.hasTag("X") && <use>))`.
- All tags in this schema share value type `Set<String>`, so you can
  use `.contains("true")`, `.containsAll(other_set)`, etc. on tag values.
