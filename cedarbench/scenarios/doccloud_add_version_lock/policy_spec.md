# Document Cloud Permissions -- Policy Specification

## Context

This policy governs access control for a document management platform with
Documents, Users, Groups, Drives, and sharing ACLs (DocumentShare).

Documents have three ACL attributes (viewACL, modifyACL, manageACL), each
referencing a DocumentShare entity that Groups and Public can be members of.
Documents also have a publicAccess string attribute and an owner reference.

## Requirements

### 1. Owner Permissions
- The **owner** of a document may perform ALL actions on that document:
  ViewDocument, ModifyDocument, DeleteDocument, EditIsPrivate, EditPublicAccess,
  AddToShareACL.

### 2. View ACL Permissions
- A user who is in a document's **viewACL** may **ViewDocument**.

### 3. Modify ACL Permissions
- A user who is in a document's **modifyACL** may **ModifyDocument**.

### 4. Manage ACL Permissions
- A user who is in a document's **manageACL** may perform:
  **AddToShareACL**, **DeleteDocument**, **EditIsPrivate**, **EditPublicAccess**.

### 5. Public Access Rules
- If a document's `publicAccess == "view"`, then **Public** principals (or any
  authenticated user) may **ViewDocument**.
- If a document's `publicAccess == "edit"`, then **Public** principals may
  **ViewDocument** and **ModifyDocument**.

### 6. Blocking Rules (Deny Rules -- Bidirectional)
- If the **principal** is in the document owner's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.
- If the document **owner** is in the principal's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.
- Blocking is bidirectional: either direction triggers the deny.

### 7. Authentication Requirement (Deny Rule)
- For **User** principals, all actions are forbidden unless
  `context.is_authenticated == true`.

### 8. Group Owner Permissions
- The **owner** of a Group may **DeleteGroup** and **ModifyGroup** on that Group.

## Notes
- ACL membership is checked via `principal in resource.viewACL` (etc.).
- The Public entity type is a separate principal type, not a User.
- Cedar denies by default -- no explicit deny-by-default policy is needed.
- Blocking forbid rules use `when` conditions on entity attribute sets.
### 9. Version Lock (Deny Rule)
- Documents have an `isLocked` boolean attribute.
- If `resource.isLocked == true`, forbid **ModifyDocument** for all users
  (including users in modifyACL and the document owner).
- **DeleteDocument** is still allowed on locked documents (the owner can delete).
- **ViewDocument** is still allowed on locked documents.
- **AddToShareACL**, **EditIsPrivate**, and **EditPublicAccess** are still allowed
  on locked documents (these are management actions, not content modification).
