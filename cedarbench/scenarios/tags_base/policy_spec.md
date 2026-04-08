# Tag- and Role-Based Access Control — Policy Specification

## Context

This policy governs access control for ABC Technologies, where principals
are `User`s and resources are `Workspace`s. The system uses a combination
of role membership and tag matching to grant access:

- A User belongs to one or more `Role`s. Each Role has an associated
  Action group that lists which actions members of that role can perform.
- A User has *role-scoped tags*: a set of tag values per (role, tag-group)
  combination. Tags are organized into tag groups (each group is
  effectively a tag key with a set of permitted string values).
- A Workspace also has tags, drawn from the same tag groups.
- A User is permitted to perform an action on a Workspace if and only if:
  1. The User is a member of some role R such that the action is in R's
     Action group, AND
  2. The User's tags-for-role-R **match** the Workspace's tags (as
     defined below).

The two roles defined in the base scenario are `Role-A` and `Role-B`. The
three tag groups are `production_status`, `country`, and `stage`.

## Tag Matching Semantics

Tag matching is unusual and must be implemented carefully. For each tag
group `T`:

- If the **User does NOT have a value for T under role R** (i.e., the
  optional `principal.allowedTagsForRole.<R>.T` attribute is absent),
  the User's tags are treated as if they were the wildcard `"ALL"` for
  T. In other words, missing user tags are *permissive*, not restrictive.
- If the **Workspace does NOT have a value for T** (i.e., the optional
  `resource.tags.T` attribute is absent), the workspace is considered to
  have no constraint on T, so any user passes for T.
- If both have values for T:
  - The match succeeds if either side contains the literal `"ALL"` (a
    wildcard tag value).
  - Otherwise, the match succeeds if **every value in the workspace's
    set is also in the user's set** (i.e., the user's tag value set is
    a superset of the workspace's tag value set).

The overall match succeeds for a (User, Role, Workspace) triple if and
only if **all three tag groups** (production_status, country, stage)
match per the rules above. The match must be checked for *every* tag
group defined in the schema, not just the ones the workspace has values
for — though groups the user is silent on (per the rules above) trivially
pass.

## Entity Model

- **User** is the principal type. Users are members of zero or more
  Roles (`User in [Role]`). Each User has:
  - `allowedTagsForRole` — a record with one optional sub-record per role
    in the system. In the base scenario, the optional fields are
    `"Role-A"?` and `"Role-B"?`. Each role's sub-record has three
    optional tag-group fields: `production_status?: Set<String>`,
    `country?: Set<String>`, and `stage?: Set<String>`.
- **Role** is a group entity used as a User parent. The two roles in the
  base scenario are `Role::"Role-A"` and `Role::"Role-B"`.
- **Workspace** is the resource type. Each Workspace has a `tags` record
  with three optional tag-group fields, mirroring the User-side schema:
  `production_status?`, `country?`, `stage?`.

## Action Model

- `Role-A Actions` is an action group; member actions are
  `UpdateWorkspace`, `DeleteWorkspace`, and `ReadWorkspace`.
- `Role-B Actions` is an action group; the only member action is
  `ReadWorkspace`.
- Concrete actions all apply to `principal: User, resource: Workspace`.

## Requirements

### 1. Role-A Permit Rule
A User who is a member of `Role::"Role-A"` may perform any action in the
`Role-A Actions` group on a Workspace, provided their `Role-A`-scoped
tags match the Workspace's tags. Concretely:

- `principal in Role::"Role-A"` AND
- `action in Action::"Role-A Actions"` AND
- For each tag group `T` in `{production_status, country, stage}`: the
  tag-match condition described above holds for the User's `Role-A` tag
  values and the Workspace's tag values.

The tag-match condition for a single tag group `T` expands to:
```
principal.allowedTagsForRole has "Role-A" &&
( !(principal.allowedTagsForRole["Role-A"] has T)
  || !(resource.tags has T)
  || principal.allowedTagsForRole["Role-A"][T].contains("ALL")
  || resource.tags[T].contains("ALL")
  || principal.allowedTagsForRole["Role-A"][T].containsAll(resource.tags[T]) )
```

### 2. Role-B Permit Rule
A User who is a member of `Role::"Role-B"` may perform any action in the
`Role-B Actions` group on a Workspace, provided their `Role-B`-scoped
tags match the Workspace's tags. The structure is identical to §1 with
"Role-A" replaced by "Role-B".

### 3. No Default Permit
- Cedar denies by default. A user with no matching role, or with a
  matching role but with tags that fail the match, is denied. There are
  no other permit rules in the base scenario.

### 4. Multi-Role Composition
- A User in both `Role-A` and `Role-B` is permitted to perform an action
  on a Workspace if **either** role's permit rule is satisfied (Cedar's
  permit rules union via `OR`). The two role rules are independent and
  do not interact.
- A User's tags for `Role-A` and `Role-B` are stored separately and may
  differ — a user may have permissive Role-A tags and restrictive
  Role-B tags, or vice versa.

## Notes
- All policies are dynamically generated: when a new role is added,
  the host application creates a new permit rule by templating a copy
  of the per-role pattern with the new role name. When a new tag is
  added, every existing per-role policy gets a new `when` clause that
  performs the tag-match check for that tag.
- Optional attributes (`?`) on `allowedTagsForRole`, on each role's
  sub-record, on each tag group, and on `Workspace.tags` must all be
  guarded with `has` before they are read, per Cedar's type-checker
  requirements. The match logic above is written to handle every
  optional path correctly.
- The `"ALL"` wildcard is a normal string value inside a `Set<String>`,
  not a special Cedar construct. The semantics is enforced entirely
  by the policy's `contains("ALL")` checks.
- The asymmetry where missing user tags are *permissive* (treated as
  `"ALL"`) but missing workspace tags are also *permissive* (treated
  as no constraint) is intentional and per the use-case writeup.
