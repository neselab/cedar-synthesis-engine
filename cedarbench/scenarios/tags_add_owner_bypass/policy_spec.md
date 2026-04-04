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
### 3. Owner Bypass for Read Access
- Workspace now has an `owner: User` attribute.
- The **owner** of a workspace may always **ReadWorkspace** on that workspace,
  regardless of role membership or tag matching.
- Specifically: `permit (principal, action == Action::"ReadWorkspace", resource) when { principal == resource.owner }`.
- This is an ADDITIONAL path to read access -- it does not replace the
  tag-based role permissions. Users who match via Role-A or Role-B tags
  still get their normal access.
- The owner bypass applies ONLY to ReadWorkspace. It does NOT grant
  UpdateWorkspace or DeleteWorkspace. For those actions, the owner must
  still qualify via Role-A tag matching.

## Notes (Owner Bypass)
- This creates a dual-path permit for ReadWorkspace: tag-matching OR ownership.
- The owner does not need to be in any Role to read their own workspace.
