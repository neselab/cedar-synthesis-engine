# Tags & Roles Workspace Permissions -- Policy Specification

## Context

This policy governs access control for a workspace platform where access is
determined by tag-based matching between Users and Workspaces, scoped by Roles.

Users belong to Roles (via `User in [Role]`). Each User has an
`allowedTagsForRole` record that specifies, per role, which tag values the
user is authorized for. Each role's tag entry may include optional sets for
`production_status`, `country`, and `stage`.

Workspaces have a `tags` record with optional sets for the same three dimensions:
`production_status`, `country`, and `stage`.

There are two roles: **Role-A** and **Role-B**. Role-A has broader permissions
(Update, Delete, Read), while Role-B has narrower permissions (Read only).

## Requirements

### 1. Role-A Permissions
- A user in **Role-A** may perform **Role-A Actions** (UpdateWorkspace,
  DeleteWorkspace, ReadWorkspace) on a workspace when ALL of the following
  tag-matching conditions are met for each tag dimension (production_status,
  country, stage):
  - If the user's `allowedTagsForRole["Role-A"]` has the tag dimension AND
    the workspace's `tags` has the same dimension, then EITHER:
    - The user's set for that dimension contains `"ALL"`, OR
    - The workspace's set for that dimension contains `"ALL"`, OR
    - The user's set for that dimension `containsAll` of the workspace's set.
  - If either the user or the workspace is missing a tag dimension, the
    check passes (access is allowed for that dimension).

### 2. Role-B Permissions
- A user in **Role-B** may perform **Role-B Actions** (ReadWorkspace only)
  on a workspace using the same tag-matching logic as Role-A, but checking
  `allowedTagsForRole["Role-B"]` instead.

## Notes
- Tag matching is checked per-dimension: each of production_status, country,
  and stage is validated independently.
- The special value `"ALL"` acts as a wildcard -- if either the user's or the
  workspace's set contains `"ALL"`, that dimension always matches.
- Missing optional tags are treated as "no restriction" (access passes).
- Cedar denies by default; no explicit deny-by-default rule is needed.
### 3. Sensitivity Level Restriction (Deny Rules)
- Workspace now has a `sensitivity: Long` attribute (values 0 through 5).
- For **Role-A** actions: if the workspace's `sensitivity > 3`, all Role-A
  actions (UpdateWorkspace, DeleteWorkspace, ReadWorkspace) are **forbidden**
  for users acting in Role-A.
- For **Role-B** actions: if the workspace's `sensitivity > 1`, all Role-B
  actions (ReadWorkspace) are **forbidden** for users acting in Role-B.
- This means Role-A users can access workspaces with sensitivity 0-3, while
  Role-B users can only access workspaces with sensitivity 0-1.
- The sensitivity check is applied IN ADDITION to the tag-matching requirements.
  Both must pass for access to be granted.

## Notes (Sensitivity)
- Two separate forbid rules are needed: one scoped to Role-A, one to Role-B.
- The forbid for Role-A: `principal in Role::"Role-A"` and `resource.sensitivity > 3`.
- The forbid for Role-B: `principal in Role::"Role-B"` and `resource.sensitivity > 1`.
