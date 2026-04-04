# Tags & Roles Workspace Permissions -- Policy Specification (Four Dimensions)

## Context

This policy governs access control for a workspace platform where access is
determined by tag-based matching between Users and Workspaces, scoped by Roles.

Users belong to Roles (via `User in [Role]`). Each User has an
`allowedTagsForRole` record that specifies, per role, which tag values the
user is authorized for. Each role's tag entry may include optional sets for
**four** dimensions: `production_status`, `country`, `stage`, and `department`.

Workspaces have a `tags` record with optional sets for the same four dimensions.

There are two roles: **Role-A** (Update, Delete, Read) and **Role-B** (Read only).

## Requirements

### 1. Role-A Permissions
- A user in **Role-A** may perform **Role-A Actions** (UpdateWorkspace,
  DeleteWorkspace, ReadWorkspace) on a workspace when ALL of the following
  tag-matching conditions are met for EACH of the four tag dimensions
  (production_status, country, stage, department):
  - If the user's `allowedTagsForRole["Role-A"]` has the tag dimension AND
    the workspace's `tags` has the same dimension, then EITHER:
    - The user's set for that dimension contains `"ALL"`, OR
    - The workspace's set for that dimension contains `"ALL"`, OR
    - The user's set for that dimension `containsAll` of the workspace's set.
  - If either the user or the workspace is missing a tag dimension, the
    check passes (access is allowed for that dimension).

### 2. Role-B Permissions
- A user in **Role-B** may perform **Role-B Actions** (ReadWorkspace only)
  using the same tag-matching logic as Role-A, but checking
  `allowedTagsForRole["Role-B"]` across all four dimensions.

## Notes
- The `department` dimension follows the exact same matching pattern as the
  other three dimensions: optional on both sides, `"ALL"` wildcard support,
  `containsAll` for strict matching.
- Each policy now needs FOUR `when` clauses (one per dimension) instead of three.
- The tag-matching pattern is replicated identically for the new dimension.
