# Document Cloud Permissions -- Policy Specification

## Context

This policy governs access control for a document management platform with
Documents, Users, Groups, Drives, and sharing ACLs (DocumentShare).

Documents have three ACL attributes (viewACL, modifyACL, manageACL), each
referencing a DocumentShare entity that Groups and Public can be members of.
Documents also have a publicAccess string attribute and an owner reference.

In this variant, the Public entity type has been removed. Only authenticated
User principals can access documents. The publicAccess attribute on Document
is unused / has no effect on authorization.

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

### 5. Public Access (Disabled)
- There are NO public access rules. The `publicAccess` attribute has no effect.
- Only Users with explicit ACL membership or ownership can access documents.

### 6. Blocking Rules (Deny Rules -- Bidirectional)
- If the **principal** is in the document owner's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.
- If the document **owner** is in the principal's **blocked** set, forbid
  **ViewDocument** and **ModifyDocument**.

### 7. Authentication Requirement (Deny Rule)
- For **User** principals, all actions are forbidden unless
  `context.is_authenticated == true`.

### 8. Group Owner Permissions
- The **owner** of a Group may **DeleteGroup** and **ModifyGroup** on that Group.

## Notes
- There is no Public principal type in this variant.
- ACL membership is checked via `principal in resource.viewACL` (etc.).
- Cedar denies by default -- no explicit deny-by-default policy is needed.
