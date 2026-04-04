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
### 9. Organization Isolation (Deny Rule with Exception)
- Users have an `org` attribute referencing an **Organization** entity.
- Document owners also have an `org` attribute (accessed via `resource.owner.org`).
- **Forbid** all document actions (ViewDocument, ModifyDocument, DeleteDocument,
  EditIsPrivate, EditPublicAccess, AddToShareACL) when the principal's org
  does not match the document owner's org:
  `when { principal.org != resource.owner.org }`.
- **Exception**: Users who are in the document's **manageACL** bypass the
  organization isolation rule. They can access documents cross-org.
  The forbid uses: `unless { principal in resource.manageACL }`.
- Public access rules are unaffected by org isolation (Public is not a User
  and has no org attribute).
- The document **owner** always passes the org check (same org as themselves).

## Notes (Organization Isolation)
- Cross-entity comparison: `principal.org != resource.owner.org` requires
  traversing principal -> org and resource -> owner -> org.
- The manageACL exception allows designated cross-org collaborators.
- Org isolation stacks with blocking rules -- both may independently forbid access.
