# Document Cloud Drive — Policy Specification

## Context

This policy governs access control for a cloud-based document sharing system,
similar to Google Drive or Dropbox. The system supports single-user workflows
across multiple devices, multi-user collaboration on shared documents, and
public hosting. It is multi-tenant and must be robust to cross-user abuse,
which is why a mutual blocklist feature exists.

## Entity Model

- **User** — the main principal. Each User has a `personalGroup` (a Group
  entity containing only that user) and a `blocked` set listing other Users
  they have blocked.
- **Public** — a special principal representing an unauthenticated request.
- **Group** — a collection of Users used for sharing. Groups have an `owner`
  (a User who can manage the group). Every User has a personal Group of size
  one. Groups belong to `DocumentShare` entities.
- **DocumentShare** — a parent entity for groups that share access to a
  particular document. Used to express viewACL / modifyACL / manageACL.
- **Document** — the core resource. Each Document has an `owner` (User), an
  `isPrivate` flag, a `publicAccess` mode (one of `"none"`, `"view"`,
  `"edit"`), and three ACL pointers: `viewACL`, `modifyACL`, and `manageACL`,
  each a `DocumentShare`.
- **Drive** — a singleton container entity representing the application root.
  `CreateDocument` and `CreateGroup` apply to the Drive resource.
- **Context** carries `is_authenticated` (Bool).

## Requirements

### 1. Authentication Gate (Forbid)
- All requests must come from an authenticated session. **Forbid** any action
  on any resource when `context.is_authenticated == false`. This forbid has
  no exceptions and applies to every action in the system.

### 2. Document Creation
- An authenticated User may **CreateDocument** on the Drive resource.
- No other restrictions apply to document creation.

### 3. View Access
A User may **ViewDocument** on a document if **any** of the following hold:
- The User is the document's `owner`, OR
- The User is a member of a Group that is in the document's `viewACL`, AND
  the document is not private (`resource.isPrivate == false`).

A `Public` principal (unauthenticated viewer) may **ViewDocument** if all of:
- `resource.publicAccess == "view"` OR `resource.publicAccess == "edit"`, AND
- `resource.isPrivate == false`.

### 4. Modify Access
A User may **ModifyDocument** if:
- The User is the document's `owner`, OR
- The User is a member of a Group in the document's `modifyACL` AND the
  document is not private (`resource.isPrivate == false`).

### 5. Delete Document (Owner-Only)
- Only the document's `owner` may **DeleteDocument**. No ACL grants this.

### 6. Sharing & Privacy Controls
- **EditIsPrivate** (toggling the document's privacy flag) may be performed
  ONLY by the document's `owner`. No ACL grants this — the right to make a
  document private/public belongs solely to the owner.
- **AddToShareACL** (adding a User or Group to one of the ACLs) and
  **EditPublicAccess** (changing the `publicAccess` mode) may be performed
  by:
  - the document's `owner`, OR
  - any User who is a member of a Group in the document's `manageACL`.

### 7. Group Management
- An authenticated User may **CreateGroup** on the Drive resource.
- **ModifyGroup** and **DeleteGroup** may be performed only by the Group's
  `owner` (i.e., `principal == resource.owner`).

### 8. Mutual Blocking (Forbid)
- If User A has blocked User B, then B must not be able to view, modify,
  delete, change privacy on, share, or change public access for any document
  owned by A. The same restriction applies symmetrically: A must not be able
  to perform those actions on documents owned by B.
- Concretely: **Forbid** any of `ViewDocument`, `ModifyDocument`,
  `DeleteDocument`, `EditIsPrivate`, `AddToShareACL`, or `EditPublicAccess`
  when both the principal and the resource owner are Users AND either has
  blocked the other:
  `principal has blocked && (resource.owner.blocked.contains(principal) ||
  principal.blocked.contains(resource.owner))`.
- The `principal has blocked` guard is required because `ViewDocument` also
  applies to the `Public` principal type, which has no `blocked` attribute.
- The blocking forbid applies to User principals only — Public principals
  are governed by the public-access rules in §3.

### 9. Private-Document Guard Rail (Forbid)
- For any resource that has an `owner` and an `isPrivate` flag, **forbid**
  any action by a non-owner principal whenever the document is private:
  `resource has owner && principal != resource.owner && resource has
  isPrivate && resource.isPrivate`.
- This is a redundant guard rail — the per-action permits in §3, §4, §6
  already enforce privacy via `unless { resource.isPrivate }` clauses — but
  it should be expressible in the policy and is the system's last line of
  defense if a permit rule is incorrect.

## Notes
- Cedar denies by default. Per-action permits grant access; the three forbid
  rules (auth, blocking, private-document guard) override permits.
- The `publicAccess == "edit"` value implies view access — anything that can
  be edited can also be viewed. The view rule for `Public` accepts both
  `"view"` and `"edit"` modes.
- Group membership is transitive: a User may be in multiple Groups, and each
  Group may be in multiple `DocumentShare` parents. Membership checks should
  use Cedar's `in` operator to traverse the hierarchy.
- The `personalGroup` invariant (every User is in their own personal Group
  of size 1) is enforced by entity construction, not by policy rules.
