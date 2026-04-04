# Tags & Roles Workspace Permissions -- Policy Specification (Combined)

## Context

This policy governs access control for a workspace platform where access is
determined by tag-based matching between Users and Workspaces, scoped by Roles.

Users belong to Roles. Each User has an `allowedTagsForRole` record. Workspaces
have tags, a `sensitivity: Long` (0-5), an `owner: User`, and an `isApproved: Bool`.

Two roles: **Role-A** (Update, Delete, Read) and **Role-B** (Read only).

## Requirements

### 1. Role-A Permissions (Tag-Based)
- A user in **Role-A** may perform **Role-A Actions** (UpdateWorkspace,
  DeleteWorkspace, ReadWorkspace) on a workspace when tag-matching passes
  for all three dimensions (production_status, country, stage):
  - Per dimension: user's set contains `"ALL"`, OR workspace's set contains
    `"ALL"`, OR user's set `containsAll` of workspace's set.
  - Missing dimensions pass automatically.

### 2. Role-B Permissions (Tag-Based)
- A user in **Role-B** may perform **Role-B Actions** (ReadWorkspace) using
  the same tag-matching logic, checking `allowedTagsForRole["Role-B"]`.

### 3. Owner Bypass for Read Access
- The **owner** of a workspace may always **ReadWorkspace** on that workspace,
  regardless of role membership or tag matching.
- The owner bypass applies ONLY to ReadWorkspace. The owner must still qualify
  via Role-A tag matching for UpdateWorkspace and DeleteWorkspace.
- The owner bypass also ignores sensitivity restrictions for read access.

### 4. Sensitivity Level Restriction (Deny Rules)
- For **Role-A** actions: if `resource.sensitivity > 3`, all Role-A actions
  are **forbidden** for users acting in Role-A.
- For **Role-B** actions: if `resource.sensitivity > 1`, all Role-B actions
  are **forbidden** for users acting in Role-B.
- **Exception**: The owner bypass for ReadWorkspace is NOT subject to sensitivity
  restrictions. If `principal == resource.owner`, ReadWorkspace is always allowed.

### 5. Approval Gate (Deny Rule)
- If `resource.isApproved == false`, **UpdateWorkspace** and **DeleteWorkspace**
  are **forbidden** for ALL users, including owners.
- **ReadWorkspace** is still allowed on unapproved workspaces.

## Notes
- Three independent forbid rules exist: Role-A sensitivity, Role-B sensitivity,
  and approval gate. They operate independently.
- The owner bypass creates a separate permit path for ReadWorkspace that is
  immune to sensitivity forbids (the forbid must use `unless { principal == resource.owner }`).
- The approval gate has no owner exception -- even workspace owners cannot
  update or delete unapproved workspaces.
- This is a complex scenario with tag matching, numeric thresholds, owner bypass,
  and boolean gates all interacting.
