"""Tags-and-roles workspace permissions mutations."""

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

# -- Base policy spec (shared starting point) ---------------------------------

_BASE_SPEC = """\
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
"""


# -- Helpers -------------------------------------------------------------------

def _tags_base_schema() -> str:
    """The base tags_n_roles schema."""
    return """\
// Tags & Roles -- Cedar Schema

entity Role;
entity User in [Role] {
  allowedTagsForRole: {
    "Role-A"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    "Role-B"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
  },
};
entity Workspace {
  tags: {
    production_status?: Set<String>,
    country?: Set<String>,
    stage?: Set<String>,
  }
};

action "Role-A Actions";
action "Role-B Actions";
action UpdateWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action DeleteWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action ReadWorkspace in ["Role-A Actions", "Role-B Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};
"""


# -- Easy Mutations ------------------------------------------------------------

class TagsAddRoleC(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_add_role_c",
            base_scenario="tags",
            difficulty="easy",
            description="Add Role-C with ArchiveWorkspace action; same tag-matching pattern",
            operators=["S7", "S9", "P2"],
            features_tested=["new_role", "new_action", "pattern_extension"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Tags & Roles -- Cedar Schema (with Role-C)

entity Role;
entity User in [Role] {
  allowedTagsForRole: {
    "Role-A"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    "Role-B"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    "Role-C"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
  },
};
entity Workspace {
  tags: {
    production_status?: Set<String>,
    country?: Set<String>,
    stage?: Set<String>,
  }
};

action "Role-A Actions";
action "Role-B Actions";
action "Role-C Actions";
action UpdateWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action DeleteWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action ReadWorkspace in ["Role-A Actions", "Role-B Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action ArchiveWorkspace in ["Role-C Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};
"""
        spec = _BASE_SPEC + """\
### 3. Role-C Permissions
- A new **Role-C** exists with a single action: **ArchiveWorkspace**.
- A user in **Role-C** may perform **ArchiveWorkspace** on a workspace using
  the same tag-matching logic as Role-A and Role-B, but checking
  `allowedTagsForRole["Role-C"]`.
- Role-C has no overlap with Role-A or Role-B actions -- ArchiveWorkspace
  is exclusive to Role-C.
- The tag-matching rules for Role-C follow the identical pattern:
  per-dimension check of production_status, country, and stage, with
  `"ALL"` wildcard support and missing-tag passthrough.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class TagsRemoveAllWildcard(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_remove_all_wildcard",
            base_scenario="tags",
            difficulty="easy",
            description='Remove "ALL" special value wildcard from tag matching',
            operators=["P3", "P8"],
            features_tested=["simplification", "strict_matching"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Schema is unchanged -- the wildcard is purely a policy-level concept
        schema = _tags_base_schema()
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Medium Mutations ----------------------------------------------------------

class TagsAddSensitivity(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_add_sensitivity",
            base_scenario="tags",
            difficulty="medium",
            description="Add sensitivity Long on Workspace; Role-A sees <= 3, Role-B sees <= 1",
            operators=["S2", "P1", "P10"],
            features_tested=["numeric_comparison", "role_differentiated_threshold"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Tags & Roles -- Cedar Schema (with Sensitivity)

entity Role;
entity User in [Role] {
  allowedTagsForRole: {
    "Role-A"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    "Role-B"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
  },
};
entity Workspace {
  tags: {
    production_status?: Set<String>,
    country?: Set<String>,
    stage?: Set<String>,
  },
  sensitivity: Long,
};

action "Role-A Actions";
action "Role-B Actions";
action UpdateWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action DeleteWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action ReadWorkspace in ["Role-A Actions", "Role-B Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};
"""
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class TagsAddOwnerBypass(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_add_owner_bypass",
            base_scenario="tags",
            difficulty="medium",
            description="Add owner User on Workspace; owner always has read access regardless of tags",
            operators=["S9", "P2", "P5"],
            features_tested=["owner_attribute", "bypass_rule", "dual_path"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Tags & Roles -- Cedar Schema (with Owner)

entity Role;
entity User in [Role] {
  allowedTagsForRole: {
    "Role-A"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    "Role-B"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
  },
};
entity Workspace {
  tags: {
    production_status?: Set<String>,
    country?: Set<String>,
    stage?: Set<String>,
  },
  owner: User,
};

action "Role-A Actions";
action "Role-B Actions";
action UpdateWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action DeleteWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action ReadWorkspace in ["Role-A Actions", "Role-B Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};
"""
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class TagsAddApproval(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_add_approval",
            base_scenario="tags",
            difficulty="medium",
            description="Add isApproved Bool on Workspace; unapproved workspaces are read-only",
            operators=["S1", "P1"],
            features_tested=["boolean_guard", "action_restriction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Tags & Roles -- Cedar Schema (with Approval)

entity Role;
entity User in [Role] {
  allowedTagsForRole: {
    "Role-A"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    "Role-B"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
  },
};
entity Workspace {
  tags: {
    production_status?: Set<String>,
    country?: Set<String>,
    stage?: Set<String>,
  },
  isApproved: Bool,
};

action "Role-A Actions";
action "Role-B Actions";
action UpdateWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action DeleteWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action ReadWorkspace in ["Role-A Actions", "Role-B Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};
"""
        spec = _BASE_SPEC + """\
### 3. Approval Gate (Deny Rule)
- Workspace now has an `isApproved: Bool` attribute.
- If a workspace has `isApproved == false`, the **UpdateWorkspace** and
  **DeleteWorkspace** actions are **forbidden** for ALL users.
- **ReadWorkspace** is still allowed on unapproved workspaces (the tag-matching
  rules still apply for read access).
- This is independent of role -- both Role-A and any other role are subject
  to this restriction.

## Notes (Approval)
- The forbid rule targets: `action in [Action::"UpdateWorkspace", Action::"DeleteWorkspace"]`
  when `resource.isApproved == false`.
- Alternatively: `forbid ... unless { resource.isApproved }` on write actions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Hard Mutations ------------------------------------------------------------

class TagsAddFourthDimension(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_add_fourth_dimension",
            base_scenario="tags",
            difficulty="hard",
            description="Add department tag dimension to both User and Workspace tag structures",
            operators=["S9", "S9", "P2", "P7"],
            features_tested=["schema_extension", "tag_dimension_scaling", "pattern_replication"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Tags & Roles -- Cedar Schema (with Department Dimension)

entity Role;
entity User in [Role] {
  allowedTagsForRole: {
    "Role-A"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
        department?: Set<String>,
    },
    "Role-B"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
        department?: Set<String>,
    },
  },
};
entity Workspace {
  tags: {
    production_status?: Set<String>,
    country?: Set<String>,
    stage?: Set<String>,
    department?: Set<String>,
  }
};

action "Role-A Actions";
action "Role-B Actions";
action UpdateWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action DeleteWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action ReadWorkspace in ["Role-A Actions", "Role-B Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};
"""
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class TagsSensitivityAndOwner(Mutation):
    def meta(self):
        return MutationMeta(
            id="tags_sensitivity_and_owner",
            base_scenario="tags",
            difficulty="hard",
            description="Combine sensitivity levels + owner bypass + approval gate",
            operators=["S2", "S9", "S1", "P1", "P2", "P5", "P10"],
            features_tested=["multi_mutation", "numeric_guard", "owner_bypass", "boolean_guard"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Tags & Roles -- Cedar Schema (Sensitivity + Owner + Approval)

entity Role;
entity User in [Role] {
  allowedTagsForRole: {
    "Role-A"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
    "Role-B"?: {
        production_status?: Set<String>,
        country?: Set<String>,
        stage?: Set<String>,
    },
  },
};
entity Workspace {
  tags: {
    production_status?: Set<String>,
    country?: Set<String>,
    stage?: Set<String>,
  },
  sensitivity: Long,
  owner: User,
  isApproved: Bool,
};

action "Role-A Actions";
action "Role-B Actions";
action UpdateWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action DeleteWorkspace in ["Role-A Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};

action ReadWorkspace in ["Role-A Actions", "Role-B Actions"] appliesTo {
  principal: User,
  resource: Workspace,
};
"""
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Registration --------------------------------------------------------------

MUTATIONS = [
    TagsAddRoleC(),
    TagsRemoveAllWildcard(),
    TagsAddSensitivity(),
    TagsAddOwnerBypass(),
    TagsAddApproval(),
    TagsAddFourthDimension(),
    TagsSensitivityAndOwner(),
]

for m in MUTATIONS:
    register(m)
