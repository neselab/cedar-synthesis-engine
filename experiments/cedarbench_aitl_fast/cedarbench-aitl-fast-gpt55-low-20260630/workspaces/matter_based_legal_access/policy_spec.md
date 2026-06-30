---
pattern: matter-based legal access
difficulty: medium
features:
  - set contains for matter assignment
  - owner-based privileged access
  - role hierarchy
domain: legal
synthesis_difficulty: 2
---

# Matter-Based Legal Access -- Policy Specification

## Context

This policy implements a law firm's matter-based access control system.
Attorneys, paralegals, and staff only see and act on documents belonging
to matters they are assigned to. Additionally, privileged documents
(attorney-client privilege) have stricter role requirements.

Principal is `User`; resource is `Document`. Four actions: `view`,
`edit`, `file`, `redact`.

## Entity Model

### User
- `role`: String -- one of `"associate"`, `"partner"`, `"paralegal"`,
  `"admin"`.
- `assignedMatters`: Set of String -- the set of matter identifiers
  this user is assigned to.

### Document
- `matter`: String -- the matter this document belongs to.
- `isPrivileged`: Bool -- whether this document is protected by
  attorney-client privilege.

## Requirements

### 1. View Access
A User may `view` a Document when their `assignedMatters` contains the
document's `matter`.

**Privileged restriction**: if the document has `isPrivileged == true`,
only users with role `"partner"` may view it. Associates, paralegals,
and admins cannot view privileged documents even if assigned to the
matter.

### 2. Edit Access
A User may `edit` a Document when:
- `assignedMatters` contains the document's `matter`, AND
- role is `"associate"` or `"partner"`.

Paralegals and admins cannot edit documents. Privileged documents
follow the same restriction as view: only partners may edit them.

### 3. File Access
A User may `file` a Document (i.e., formally file it into the matter
record system) when:
- `assignedMatters` contains the document's `matter`.

Any role (`"paralegal"`, `"associate"`, `"partner"`, `"admin"`) may
file a document to which they are assigned. Privileged documents follow
the same restriction: only partners may file privileged documents.

### 4. Redact Access
A User may `redact` a Document when:
- `assignedMatters` contains the document's `matter`, AND
- role is `"partner"`.

Only partners can redact documents. This applies to both privileged
and non-privileged documents.

## Notes

- Matter assignment is the universal gate: no action is possible on a
  document whose matter is not in the user's `assignedMatters` set.
- The privileged-document restriction (partner-only) applies uniformly
  across all actions. A privileged document can only be viewed, edited,
  filed, or redacted by a partner assigned to the matter.
- Cedar's `Set.contains()` is used to test matter membership.
- Common failure modes: (a) forgetting the matter-assignment check on
  some action, (b) allowing non-partners to access privileged documents,
  (c) permitting edit by paralegals or admins.
