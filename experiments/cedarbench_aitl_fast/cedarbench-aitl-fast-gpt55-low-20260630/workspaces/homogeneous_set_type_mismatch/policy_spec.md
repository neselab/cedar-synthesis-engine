---
pattern: homogeneous set literals (validator constraint)
difficulty: medium
features:
  - homogeneous set literal of entity references `[Group::"a", Group::"b", Group::"c"]`
  - homogeneous set literal of strings `["share-allowed", "public"]`
  - `principal in [...]` with explicit Group entity list
  - `Set<String>.containsAny([...])` with string literal set
domain: collaboration / group access
synthesis_difficulty: 3
---

# Homogeneous Set Type Mismatch — Policy Specification

## Context

A collaboration system where Documents are accessible via Group membership
and via per-document alias tags. Policies use Cedar **set literals** in two
common shapes:

1. A list of explicitly-named privileged Group entities (used with `in`).
2. A list of string alias tags (used with `.containsAny(...)`).

This scenario exercises Cedar's **set-homogeneity validator constraint**:
every set literal that appears in a policy must contain elements of a
single type. Mixing types — for example writing
`[principal, "admin"]` (an entity reference plus a string) or `[]`
(empty set with no inferable element type) — is rejected by the
validator.

The synthesizer must therefore:
- Group together the privileged Group references in one homogeneous
  entity-set literal (`[Group::"admins", Group::"auditors", Group::"compliance"]`).
- Group together the alias-tag strings in one homogeneous string-set literal
  (`["share-allowed", "public"]`).
- Never combine entity references and strings in the same literal.

## Entities

- `User` with `id: String`.
- `Group` with `members: Set<User>` and `aliases: Set<String>`.
- `Document` with `owner: User`, `members: Set<User>`, and
  `aliases: Set<String>`.

## Actions

- `view` — read-only viewing of a Document.
- `share` — re-sharing the Document with others.

## Requirements

### 1. View Access

A User may `view` a Document when ANY of the following hold:

- The principal is a member of one of the explicitly-named privileged
  groups: `principal in [Group::"admins", Group::"auditors", Group::"compliance"]`.
- The document's owner is a member of one of those same privileged
  groups (`resource.owner in [...]`). This propagates trust from the owner.
- The principal is the document's owner (`principal == resource.owner`).

### 2. Share Access

A User may `share` a Document when **both** of the following hold:

- Membership: the principal is in the document's `members` set
  (`resource.members.contains(principal)`) OR the principal is the
  document's owner (`principal == resource.owner`).
- Alias gate: the document's `aliases` set has any overlap with the
  allowlisted alias-tag strings:
  `resource.aliases.containsAny(["share-allowed", "public"])`.

### 3. Default Deny

All other requests are denied.

## Validator Notes (LLM trap)

- `[User::"a", "b"]` mixes entity references and strings — REJECTED.
- `[principal, "admin"]` mixes entity reference and string — REJECTED.
- `[]` has no inferable element type — REJECTED.
- `[Group::"admins", Group::"auditors", Group::"compliance"]` — VALID.
- `["share-allowed", "public"]` — VALID.
