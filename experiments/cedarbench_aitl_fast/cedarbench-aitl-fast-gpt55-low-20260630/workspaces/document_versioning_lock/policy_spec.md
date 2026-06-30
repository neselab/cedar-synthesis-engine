---
pattern: document versioning lock
difficulty: medium
features:
  - boolean lock flag
  - owner-based lock control
  - version state gating
domain: content management
synthesis_difficulty: 3
---

# Document Versioning Lock — Policy Specification

## Context

This policy governs a content management system where documents can be
locked for exclusive editing and must be in draft state before publishing.
The lock mechanism prevents concurrent edits: only the lock holder (or an
admin) can modify a locked document.

Principal is `User`; resource is `Document`. There are five actions:
`read`, `edit`, `lock`, `unlock`, `publish`.

## Entity Model

- **User**: the principal. Has a `role` attribute:
  - `"viewer"` — read-only access.
  - `"editor"` — can read, edit (subject to lock), and lock documents.
  - `"admin"` — full access including unlock-override and publish.
- **Document**: the resource. Each Document has:
  - `isLocked: Bool` — whether the document is currently locked for
    exclusive editing.
  - `lockedBy: User` — the user who holds the lock. Only meaningful
    when `isLocked` is true, but always present in the schema.
  - `isDraft: Bool` — whether the document is in draft state. Only
    draft documents can be published.

## Requirements

### 1. Read (Any User)
- Any user regardless of role (viewer, editor, admin) may `read` any
  document.
- There are no restrictions on read access based on document state.

### 2. Edit (Editor/Admin + Lock Bypass)
- A user with role `"editor"` or `"admin"` may `edit` a document,
  provided the document is NOT locked, OR the document is locked by
  this user.
- Concretely: permit `edit` when `(principal.role == "editor" ||
  principal.role == "admin") && (!resource.isLocked ||
  resource.lockedBy == principal)`.
- Viewers may never edit. Editors/admins may not edit a document
  locked by someone else.

### 3. Lock (Editor/Admin)
- A user with role `"editor"` or `"admin"` may `lock` a document to
  acquire exclusive edit access.
- There is no restriction on locking an already-locked document (the
  host application handles lock state transitions; the policy only
  gates who may attempt the action).
- Concretely: permit `lock` when `principal.role == "editor" ||
  principal.role == "admin"`.

### 4. Unlock (Lock Holder or Admin)
- A user may `unlock` a document if they are the one who locked it
  (`principal == resource.lockedBy`) OR they are an admin
  (`principal.role == "admin"`).
- This allows admins to break locks held by other users (e.g., if an
  editor is unavailable).
- Concretely: permit `unlock` when `principal == resource.lockedBy ||
  principal.role == "admin"`.

### 5. Publish (Admin + Draft Only)
- Only admins may `publish` a document, and only when the document is
  in draft state.
- Concretely: permit `publish` when `principal.role == "admin" &&
  resource.isDraft`.
- Editors and viewers may never publish.

## Notes
- The lock-bypass condition on edit (`!resource.isLocked ||
  resource.lockedBy == principal`) is the central safety property.
  A candidate that permits any editor/admin to edit locked documents
  regardless of lock holder is incorrect.
- The unlock rule is intentionally broader than "only lock holder":
  admins can override. This models real-world scenarios where an
  administrator needs to release a stale lock.
- Cedar denies by default, so any action/role combination not
  explicitly permitted is denied.
- Role is modeled as a String attribute, not entity membership, to
  avoid the §8.6 role-intersection trap.
