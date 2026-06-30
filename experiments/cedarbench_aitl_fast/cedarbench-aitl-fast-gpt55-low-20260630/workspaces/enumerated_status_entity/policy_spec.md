---
pattern: enumerated entity status lifecycle
difficulty: medium
features:
  - enumerated entity types
  - entity equality (==)
  - lifecycle / state machine
  - role-based gating
domain: document management
synthesis_difficulty: 3
---

# Enumerated Status Entity — Document Lifecycle

## Background

A document management system tracks each document's current lifecycle status
using a Cedar **enumerated entity type**. Statuses are restricted to a closed
set of literals — `active`, `pending`, and `archived` — and the validator
rejects any reference to an enum value outside that set. Enum entities have
no attributes, no ancestors, and no tags; only their EID matters.

This scenario exercises Cedar's enumerated entity type feature and tests
that policies correctly compare against enum literals using `==`.

## Entities

- `Status` — enum with EIDs `"active"`, `"pending"`, `"archived"`.
- `User { role: String }` — role is freeform; `"admin"` is the only
  role that unlocks privileged actions.
- `Document { currentStatus: Status }` — every document carries a current
  status drawn from the enum.

## Actions

- `view` — read the document.
- `archive` — transition `active` → `archived`.
- `reactivate` — transition `archived` → `active`.

## Authorization rules

1. **view**
   - Any user may view a document whose `currentStatus == Status::"active"`.
   - Only an `admin` may view a document whose `currentStatus` is
     `Status::"pending"` or `Status::"archived"`.

2. **archive**
   - Only an `admin` may invoke `archive`, and only when the document's
     `currentStatus == Status::"active"`. (You cannot archive a document
     that is already archived or still pending.)

3. **reactivate**
   - Only an `admin` may invoke `reactivate`, and only when the document's
     `currentStatus == Status::"archived"`. (You cannot reactivate an
     active or pending document.)

## Notes for synthesizers

- Enum entity literals are written `Status::"active"` (etc.). Comparison
  uses `==` on entity references.
- Enum entities have NO attributes — do not attempt `Status::"active".name`
  or any other field access.
- The set of valid EIDs is closed: `Status::"draft"` would be rejected
  by the validator.
