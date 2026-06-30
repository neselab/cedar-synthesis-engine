---
pattern: deep entity hierarchy (5-level transitive membership)
difficulty: medium
features:
  - 5-level entity hierarchy (Employee in Team in Department in Division in Organization)
  - transitive `in` for group membership checks
  - classification-based access restriction
  - hierarchy-level-based permissions (division heads vs department heads)
domain: enterprise / HR
synthesis_difficulty: 2
---

# Deep Entity Hierarchy — Policy Specification

## Context

An enterprise document management system with a 5-level organizational
hierarchy:

    Employee  →  Team  →  Department  →  Division  →  Organization

Each level uses Cedar's `in` membership relation, so an Employee who is
`in` a Team is transitively `in` that Team's Department, Division, and
Organization.

Documents are owned by a Team and have a classification level
(`"public"`, `"internal"`, `"confidential"`).

## Requirements

### 1. View Access — Same Division

An Employee may **view** a Document when:
- The Employee is in the same Division as the document's owner team
  (i.e. `principal in` some Division entity that the `resource.ownerTeam`
  is also `in`), AND
- The document's classification is `"public"` or `"internal"`.

Since Cedar's `in` is transitive, `principal in resource.ownerTeam`
covers "same team," but for "same division" we need a broader check.
Use the simplification: the schema already encodes that Teams are in
Departments which are in Divisions. So use:
- For same-team: `principal in resource.ownerTeam`
- For confidential: only same-team members

For `"public"` and `"internal"` documents, any Employee in the
organization may view them (no hierarchy restriction).

**Simplified rule:** An Employee may view a Document when:
- The document classification is `"public"` (any employee), OR
- The document classification is `"internal"` (any employee), OR
- The document classification is `"confidential"` AND
  `principal in resource.ownerTeam` (same-team members only).

### 2. Edit Access — Same Team Only

An Employee may **edit** a Document when:
- `principal in resource.ownerTeam` (the employee belongs to the
  owning team, directly or transitively), AND
- The document classification is NOT `"confidential"`. Confidential
  documents cannot be edited (they are view-only for the owning team).

### 3. Delete Access — Same Team + Public Only

An Employee may **delete** a Document when:
- `principal in resource.ownerTeam`, AND
- The document classification is `"public"`.

Only public documents owned by the team can be deleted. Internal and
confidential documents require an admin workflow outside this policy.

### 4. Default Deny

All other requests are denied. There is no global admin bypass in this
policy.
