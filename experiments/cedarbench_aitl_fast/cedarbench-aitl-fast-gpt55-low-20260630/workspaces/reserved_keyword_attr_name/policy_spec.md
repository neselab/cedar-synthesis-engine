---
pattern: Slack-style messaging with attributes near Cedar reserved keywords
difficulty: medium
features:
  - attribute names that flirt with Cedar reserved-word space
  - public-channel fallback access via boolean flag
  - capability-set scoping for write/admin actions
  - membership via Set<Entity> (symcc-friendly)
domain: messaging / collaboration
synthesis_difficulty: 3
---

# Reserved-Keyword-Adjacent Attribute Names — Policy Specification

## Context

A Slack-style team-messaging platform. `Member` principals interact with
`Channel` resources (`read`, `post`, `pin`).

The attribute names on `Member` and `Channel` are deliberately chosen to be
*close to* Cedar reserved keywords without actually being reserved. Cedar
rejects bare `in`, `has`, `like`, `if`, `then`, `else`, `true`, `false`, `is`
as identifiers in schemas, but accepts substring/affix variants like
`inGroup`, `hasAccess`, `likedItems`. This scenario tests whether a synthesizer
can correctly use these "trap" attribute names without slipping into bare
reserved words and producing parse errors.

## Schema (must use exactly these attribute names)

`Member`:
- `inGroup: Set<String>` — informational group memberships (e.g. `"design"`,
  `"eng"`). Trap-word: looks like `in`.
- `hasAccess: Bool` — global flag enabling public-channel access. Trap-word:
  looks like `has`.
- `likedItems: Set<String>` — feature-affinity tags collected from prior
  activity (e.g. `"pinning"`). Trap-word: looks like `like`.
- `permits: Set<String>` — capability set (e.g. `"post"`, `"pin"`). Trap-word:
  looks like `permit`.

`Channel`:
- `members: Set<Member>` — explicit member set, used for `contains` (NOT
  entity-graph `in`, per §8.10).
- `isPublic: Bool` — whether non-members with `hasAccess` may read.

## Requirements

### 1. Read — Members or Public+HasAccess
A `Member` may `read` a `Channel` when ANY of:
- `resource.members.contains(principal)`, OR
- `resource.isPublic && principal.hasAccess`.

### 2. Post — Members with `"post"` Capability
A `Member` may `post` to a `Channel` when ALL of:
- `resource.members.contains(principal)`, AND
- `principal.permits.contains("post")`.

### 3. Pin — Members with `"pin"` Capability AND Pinning Affinity
A `Member` may `pin` in a `Channel` when ALL of:
- `resource.members.contains(principal)`, AND
- `principal.permits.contains("pin")`, AND
- `principal.likedItems.contains("pinning")`.

The `likedItems` check models a UX-side heuristic: the platform only exposes
the pin action to members who have engaged with pinning before.

### 4. Default Deny
All other requests are denied. Non-members with no public+hasAccess fallback
cannot read. Members without the right capability cannot post or pin. Members
with the right capability but no pinning affinity cannot pin.

## Note on attribute naming

The attribute names are chosen so that a careless synthesizer might write
bare `principal.in.contains(...)`, `principal.has`, or `principal.like`,
all of which are parse errors at the policy level (and would be rejected
at the schema level too). The reference policies use only the
declared trap-adjacent names.
