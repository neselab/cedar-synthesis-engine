# Tags & Roles Workspace Permissions -- Policy Specification (Strict Matching)

## Context

This policy governs access control for a workspace platform where access is
determined by tag-based matching between Users and Workspaces, scoped by Roles.

Users belong to Roles (via `User in [Role]`). Each User has an
`allowedTagsForRole` record that specifies, per role, which tag values the
user is authorized for. Workspaces have a `tags` record with optional sets
for production_status, country, and stage.

There are two roles: **Role-A** (Update, Delete, Read) and **Role-B** (Read only).

## Requirements

### 1. Role-A Permissions
- A user in **Role-A** may perform **Role-A Actions** (UpdateWorkspace,
  DeleteWorkspace, ReadWorkspace) on a workspace when ALL of the following
  tag-matching conditions are met for each tag dimension (production_status,
  country, stage):
  - If the user's `allowedTagsForRole["Role-A"]` has the tag dimension AND
    the workspace's `tags` has the same dimension, then the user's set for
    that dimension must `containsAll` of the workspace's set.
  - If either the user or the workspace is missing a tag dimension, the
    check passes (access is allowed for that dimension).

### 2. Role-B Permissions
- A user in **Role-B** may perform **Role-B Actions** (ReadWorkspace only)
  using the same strict tag-matching logic as Role-A, but checking
  `allowedTagsForRole["Role-B"]`.

## Notes
- There is NO `"ALL"` wildcard in this variant. The only way to match a tag
  dimension is for the user's set to literally contain all values in the
  workspace's set via `containsAll`.
- Missing optional tags are still treated as "no restriction" (access passes).
- The `"ALL"` string value, if present in data, has no special meaning and is
  treated as a regular tag value.
