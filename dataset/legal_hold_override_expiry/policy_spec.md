# Legal Hold Override Expiry — Policy Specification

## Context

This policy governs a records management system with two interacting
concepts: **document expiry** (documents auto-archive after an
`expiryDate` and become read-only) and **legal hold** (an override flag
that prevents auto-archive and preserves edit access for the legal
team). The interplay between these two is the central challenge.

Principal is `User`; resource is `Document`. Three actions: `readDocument`,
`editDocument`, `deleteDocument`. Context carries `now.datetime`.

## Requirements

### 1. Owner Baseline Access
- The document's owner may always `readDocument`. Reading is never
  blocked by expiry or legal hold.
- Specifically: permit `readDocument` when `principal == resource.owner`.

### 2. Legal Team Baseline Read Access
- Any legal team member (`principal.isLegalTeam == true`) may always
  `readDocument`, regardless of expiry or ownership.

### 3. Edit Access (Owner, Pre-Expiry)
- The document's owner may `editDocument` ONLY when the document has
  not yet expired: `context.now.datetime < resource.expiryDate`.
- Once the document's expiry has passed, the owner loses edit access
  automatically.

### 4. Delete Access (Owner, Pre-Expiry, No Legal Hold)
- The document's owner may `deleteDocument` ONLY when ALL of:
  - The document has not yet expired, AND
  - The document is NOT under a legal hold.
- A legal hold blocks deletion entirely, regardless of expiry status.

### 5. Legal Hold Override — Edit
- A legal team member (`principal.isLegalTeam == true`) may
  `editDocument` on a Document that is under a legal hold
  (`resource.legalHold == true`), regardless of the expiry date. This
  is the central override: legal hold preserves edit access past expiry.
- For non-legal-hold documents, legal team members do NOT get edit
  access — they only have the baseline read access from §2.

### 6. No Legal Hold Override for Deletion
- Legal team members have NO deletion authority, even for documents
  under a legal hold. Deletion is strictly an owner action (per §4),
  and legal hold blocks it entirely.
- This means a document under a legal hold can never be deleted by
  anyone until the hold is lifted.

## Notes
- The interplay: without legal hold, the owner has full read/edit/delete
  access until expiry, and only read access afterwards. With legal hold,
  the owner loses delete access entirely, and the legal team gains edit
  access past expiry.
- Cedar denies by default. The permits above grant access; no explicit
  forbid is required because the conditions are expressed inside each
  permit's `when` clause. A defensive forbid on
  (expired AND !(legal team AND legal hold)) for edit is acceptable but
  redundant.
- Common failure modes: (a) allowing legal team to edit ANY document
  (missing the legal-hold precondition), (b) allowing legal team to
  delete (missing §6), (c) forgetting that legal hold also blocks
  owner deletion (§4's second clause).
