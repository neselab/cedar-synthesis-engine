"""GitHub repository permissions mutations."""

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

# ── Base policy spec (shared starting point) ─────────────────────────────────

_BASE_SPEC = """\
# GitHub Repository Permissions — Policy Specification

## Context

This policy governs access control for a GitHub-like platform with
Organizations, Repositories, Issues, Users, and Teams.

Repositories have five role tiers, represented as UserGroup attributes:
readers, triagers, writers, maintainers, and admins.

## Requirements

### 1. Reader Permissions
- A user who is a **reader** of a repository may **pull** and **fork** that repository.
- A reader may **delete** or **edit** an issue ONLY if they are also the **reporter** of that issue.

### 2. Triager Permissions
- A user who is a **triager** may **assign** issues in a repository.

### 3. Writer Permissions
- A user who is a **writer** may **push** to a repository.
- A writer may **edit** any issue in a repository (regardless of who reported it).

### 4. Maintainer Permissions
- A user who is a **maintainer** may **delete** any issue in a repository (regardless of who reported it).

### 5. Admin Permissions
- A user who is an **admin** may add users to any role: add_reader, add_triager, add_writer, add_maintainer, add_admin.

### 6. Archived Repository Block (Deny Rule)
- If a repository is archived (`isArchived == true`), no **write operations** are allowed.
  Write operations include: push, add_reader, add_writer, add_maintainer, add_admin, add_triager.
- Read operations (pull, fork) remain allowed on archived repos.
- Issue operations are unaffected by archive status.

## Notes
- Roles are checked via entity group membership: `principal in resource.readers` (for repo actions)
  or `principal in resource.repo.readers` (for issue actions, traversing Issue → Repository).
- There is no explicit deny-by-default policy needed — Cedar denies by default.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _github_base_schema() -> str:
    """The base GitHub schema with isArchived."""
    return """\
// GitHub Repository Permissions — Cedar Schema

entity Team, UserGroup in [UserGroup];

entity Issue = {
    repo: Repository,
    reporter: User,
};

entity Org = {
    members: UserGroup,
    owners: UserGroup,
};

entity Repository = {
    readers: UserGroup,
    triagers: UserGroup,
    writers: UserGroup,
    maintainers: UserGroup,
    admins: UserGroup,
    isArchived: Bool,
};

entity User in [UserGroup, Team];

// Repository actions
action pull, push, fork appliesTo {
    principal: [User],
    resource: [Repository],
};

// Issue actions
action assign_issue, delete_issue, edit_issue appliesTo {
    principal: [User],
    resource: [Issue],
};

// Admin actions
action add_reader, add_writer, add_maintainer, add_admin, add_triager appliesTo {
    principal: [User],
    resource: [Repository],
};
"""


# ── Easy Mutations ────────────────────────────────────────────────────────────

class GitHubAddPrivate(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_add_private",
            base_scenario="github",
            difficulty="easy",
            description="Add isPrivate boolean to Repository; forbid fork on private repos",
            operators=["S1", "P1"],
            features_tested=["boolean_guard", "forbid_rule"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "isPrivate", "Bool")
        spec = _BASE_SPEC + """\
### 7. Private Repository Restriction (Deny Rule)
- If a repository is private (`isPrivate == true`), the **fork** action is forbidden.
- All other actions are unaffected by the private flag (readers can still pull, writers can still push, etc.).
- This is independent of the archive rule — a repo can be both private and archived.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubAddCloseIssue(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_add_close_issue",
            base_scenario="github",
            difficulty="easy",
            description="Add close_issue action; Writer+ can close any, Reader can close own",
            operators=["S7", "P2", "P5"],
            features_tested=["new_action", "dual_path"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = base_schema.replace(
            "action assign_issue, delete_issue, edit_issue appliesTo {",
            "action assign_issue, delete_issue, edit_issue, close_issue appliesTo {"
        )
        spec = _BASE_SPEC.replace(
            "### 2. Triager Permissions",
            """\
### 1b. Close Issue Permissions
- A **writer** (or above) may **close** any issue in a repository.
- A **reader** may **close** an issue ONLY if they are the **reporter** of that issue.
  (Same dual-path pattern as edit/delete.)

### 2. Triager Permissions"""
        )
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubRemoveTriager(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_remove_triager",
            base_scenario="github",
            difficulty="easy",
            description="Remove Triager role; assign_issue moves to Writer tier",
            operators=["S10", "P3", "P8"],
            features_tested=["role_redistribution"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.remove_attribute(base_schema, "Repository", "triagers")
        # Remove add_triager from admin actions
        schema = schema.replace(
            "action add_reader, add_writer, add_maintainer, add_admin, add_triager appliesTo {",
            "action add_reader, add_writer, add_maintainer, add_admin appliesTo {"
        )
        spec = """\
# GitHub Repository Permissions — Policy Specification

## Context

This policy governs access control for a GitHub-like platform with
Organizations, Repositories, Issues, Users, and Teams.

Repositories have four role tiers, represented as UserGroup attributes:
readers, writers, maintainers, and admins. (There is no triager role.)

## Requirements

### 1. Reader Permissions
- A user who is a **reader** of a repository may **pull** and **fork** that repository.
- A reader may **delete** or **edit** an issue ONLY if they are also the **reporter** of that issue.

### 2. Writer Permissions
- A user who is a **writer** may **push** to a repository.
- A writer may **edit** any issue in a repository (regardless of who reported it).
- A writer may **assign** issues in a repository (previously a triager responsibility).

### 3. Maintainer Permissions
- A user who is a **maintainer** may **delete** any issue in a repository (regardless of who reported it).

### 4. Admin Permissions
- A user who is an **admin** may add users to any role: add_reader, add_writer, add_maintainer, add_admin.

### 5. Archived Repository Block (Deny Rule)
- If a repository is archived (`isArchived == true`), no **write operations** are allowed.
  Write operations include: push, add_reader, add_writer, add_maintainer, add_admin.
- Read operations (pull, fork) remain allowed on archived repos.
- Issue operations are unaffected by archive status.

## Notes
- Roles are checked via entity group membership: `principal in resource.readers` (for repo actions)
  or `principal in resource.repo.readers` (for issue actions, traversing Issue → Repository).
- There is no explicit deny-by-default policy needed — Cedar denies by default.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubAddLockedIssue(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_add_locked_issue",
            base_scenario="github",
            difficulty="easy",
            description="Add isLocked boolean to Issue; forbid edit_issue on locked issues",
            operators=["S1", "P1"],
            features_tested=["boolean_guard", "forbid_permit_interaction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Issue", "isLocked", "Bool")
        spec = _BASE_SPEC + """\
### 7. Locked Issue Block (Deny Rule)
- If an issue is locked (`isLocked == true`), the **edit_issue** action is forbidden for all users.
- **delete_issue** and **assign_issue** are still allowed on locked issues.
- This is independent of the archive rule and role-based permissions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubNoArchive(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_no_archive",
            base_scenario="github",
            difficulty="easy",
            description="Remove isArchived and archive forbid rule; pure RBAC baseline",
            operators=["S1", "P3"],
            features_tested=["pure_rbac", "simplification"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.remove_attribute(base_schema, "Repository", "isArchived")
        spec = """\
# GitHub Repository Permissions — Policy Specification

## Context

This policy governs access control for a GitHub-like platform with
Organizations, Repositories, Issues, Users, and Teams.

Repositories have five role tiers, represented as UserGroup attributes:
readers, triagers, writers, maintainers, and admins.

## Requirements

### 1. Reader Permissions
- A user who is a **reader** of a repository may **pull** and **fork** that repository.
- A reader may **delete** or **edit** an issue ONLY if they are also the **reporter** of that issue.

### 2. Triager Permissions
- A user who is a **triager** may **assign** issues in a repository.

### 3. Writer Permissions
- A user who is a **writer** may **push** to a repository.
- A writer may **edit** any issue in a repository (regardless of who reported it).

### 4. Maintainer Permissions
- A user who is a **maintainer** may **delete** any issue in a repository (regardless of who reported it).

### 5. Admin Permissions
- A user who is an **admin** may add users to any role: add_reader, add_triager, add_writer, add_maintainer, add_admin.

## Notes
- Roles are checked via entity group membership: `principal in resource.readers` (for repo actions)
  or `principal in resource.repo.readers` (for issue actions, traversing Issue → Repository).
- There is no explicit deny-by-default policy needed — Cedar denies by default.
- There are no deny rules in this scenario — it is pure RBAC.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Medium Mutations ──────────────────────────────────────────────────────────

class GitHubAddPullRequest(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_add_pullrequest",
            base_scenario="github",
            difficulty="medium",
            description="Add PullRequest entity with merge_pr and approve_pr actions; author cannot approve own PR",
            operators=["S6", "S7", "S7", "P2", "P2", "P1"],
            features_tested=["new_entity", "cross_entity_traversal", "self_exclusion"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity PullRequest = {
    repo: Repository,
    author: User,
};""")
        schema = schema_ops.add_action(schema, """\
// Pull request actions
action merge_pr, approve_pr appliesTo {
    principal: [User],
    resource: [PullRequest],
};""")
        spec = _BASE_SPEC + """\
### 7. Pull Request Permissions
- A **writer** (or above: maintainer, admin) of the pull request's repository may **merge** the pull request.
- A **reader** (or above) of the pull request's repository may **approve** the pull request.
- However, the **author** of a pull request may NOT **approve** their own pull request (self-approval is forbidden).
- Merging is blocked on archived repositories (same as other write operations).

## Notes (Pull Requests)
- Pull request roles are checked via cross-entity traversal: `principal in resource.repo.writers`.
- The self-approval block requires: `forbid ... when { principal == resource.author }`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubAddContributor(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_add_contributor",
            base_scenario="github",
            difficulty="medium",
            description="Add Contributor role between Triager and Writer; can push but not edit issues",
            operators=["S9", "P2", "P7"],
            features_tested=["role_hierarchy", "fine_grained_roles"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "contributors", "UserGroup")
        spec = """\
# GitHub Repository Permissions — Policy Specification

## Context

This policy governs access control for a GitHub-like platform with
Organizations, Repositories, Issues, Users, and Teams.

Repositories have six role tiers, represented as UserGroup attributes:
readers, triagers, contributors, writers, maintainers, and admins.

## Requirements

### 1. Reader Permissions
- A user who is a **reader** of a repository may **pull** and **fork** that repository.
- A reader may **delete** or **edit** an issue ONLY if they are also the **reporter** of that issue.

### 2. Triager Permissions
- A user who is a **triager** may **assign** issues in a repository.

### 3. Contributor Permissions
- A user who is a **contributor** may **push** to a repository.
- Contributors may NOT edit or delete issues (unless they are the reporter and a reader).

### 4. Writer Permissions
- A user who is a **writer** may **push** to a repository.
- A writer may **edit** any issue in a repository (regardless of who reported it).

### 5. Maintainer Permissions
- A user who is a **maintainer** may **delete** any issue in a repository (regardless of who reported it).

### 6. Admin Permissions
- A user who is an **admin** may add users to any role: add_reader, add_triager, add_writer, add_maintainer, add_admin.

### 7. Archived Repository Block (Deny Rule)
- If a repository is archived (`isArchived == true`), no **write operations** are allowed.
  Write operations include: push, add_reader, add_writer, add_maintainer, add_admin, add_triager.
- Read operations (pull, fork) remain allowed on archived repos.
- Issue operations are unaffected by archive status.

## Notes
- Roles are checked via entity group membership.
- Contributors share the push permission with writers, but do NOT get issue-editing privileges.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubPrivateAndLocked(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_private_and_locked",
            base_scenario="github",
            difficulty="medium",
            description="Add isPrivate on Repo (forbid fork) + isLocked on Issue (forbid edit); two independent forbids",
            operators=["S1", "S1", "P1", "P1"],
            features_tested=["multi_forbid", "boolean_guards"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "isPrivate", "Bool")
        schema = schema_ops.add_attribute(schema, "Issue", "isLocked", "Bool")
        spec = _BASE_SPEC + """\
### 7. Private Repository Restriction (Deny Rule)
- If a repository is private (`isPrivate == true`), the **fork** action is forbidden.
- All other actions are unaffected by the private flag.

### 8. Locked Issue Block (Deny Rule)
- If an issue is locked (`isLocked == true`), the **edit_issue** action is forbidden for all users.
- **delete_issue** and **assign_issue** are still allowed on locked issues.

## Notes (Multiple Forbid Rules)
- This scenario has THREE independent forbid rules: archive block, private block, and locked block.
- Each forbid operates on a different entity type and blocks different actions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubAddVisibility(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_add_visibility",
            base_scenario="github",
            difficulty="medium",
            description="Replace isArchived with visibility string (public/private/internal); multi-value conditions",
            operators=["S3", "P1", "P7"],
            features_tested=["string_enum", "multi_value_condition"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.remove_attribute(base_schema, "Repository", "isArchived")
        schema = schema_ops.add_attribute(schema, "Repository", "visibility", "String")
        spec = """\
# GitHub Repository Permissions — Policy Specification

## Context

This policy governs access control for a GitHub-like platform with
Organizations, Repositories, Issues, Users, and Teams.

Repositories have five role tiers (readers, triagers, writers, maintainers, admins)
and a `visibility` attribute with three possible values: `"public"`, `"private"`, `"internal"`.

## Requirements

### 1. Reader Permissions
- A user who is a **reader** of a repository may **pull** and **fork** that repository.
- A reader may **delete** or **edit** an issue ONLY if they are also the **reporter** of that issue.

### 2. Triager Permissions
- A user who is a **triager** may **assign** issues in a repository.

### 3. Writer Permissions
- A user who is a **writer** may **push** to a repository.
- A writer may **edit** any issue in a repository (regardless of who reported it).

### 4. Maintainer Permissions
- A user who is a **maintainer** may **delete** any issue in a repository (regardless of who reported it).

### 5. Admin Permissions
- A user who is an **admin** may add users to any role: add_reader, add_triager, add_writer, add_maintainer, add_admin.

### 6. Visibility Rules (Deny Rules)
- If a repository's visibility is `"private"`, the **fork** action is forbidden.
- If a repository's visibility is `"internal"`, the **fork** action is forbidden.
  (Only `"public"` repositories can be forked.)
- All other actions are unaffected by visibility — readers can still pull, writers can still push, etc.

## Notes
- This scenario uses a String attribute with enum-like values instead of boolean flags.
- There are no archive-related rules in this variant.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubAddSecurityAdmin(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_add_security_admin",
            base_scenario="github",
            difficulty="medium",
            description="Add SecurityAdmin role that can push to archived repos (unless exception on forbid)",
            operators=["S9", "P4"],
            features_tested=["unless_exception", "role_forbid_bypass"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "securityAdmins", "UserGroup")
        spec = """\
# GitHub Repository Permissions — Policy Specification

## Context

This policy governs access control for a GitHub-like platform with
Organizations, Repositories, Issues, Users, and Teams.

Repositories have six role tiers: readers, triagers, writers, maintainers, admins,
and a special **securityAdmins** role.

## Requirements

### 1. Reader Permissions
- A user who is a **reader** of a repository may **pull** and **fork** that repository.
- A reader may **delete** or **edit** an issue ONLY if they are also the **reporter** of that issue.

### 2. Triager Permissions
- A user who is a **triager** may **assign** issues in a repository.

### 3. Writer Permissions
- A user who is a **writer** may **push** to a repository.
- A writer may **edit** any issue in a repository (regardless of who reported it).

### 4. Maintainer Permissions
- A user who is a **maintainer** may **delete** any issue in a repository (regardless of who reported it).

### 5. Admin Permissions
- A user who is an **admin** may add users to any role: add_reader, add_triager, add_writer, add_maintainer, add_admin.

### 6. Security Admin Permissions
- A **securityAdmin** may **push** to a repository (same as writer).
- Security admins are EXEMPT from the archive block — they can push even to archived repos.

### 7. Archived Repository Block (Deny Rule with Exception)
- If a repository is archived (`isArchived == true`), no write operations are allowed
  (push, add_reader, add_writer, add_maintainer, add_admin, add_triager).
- **Exception**: Security admins (`principal in resource.securityAdmins`) bypass this block for `push`.
  The archive block still applies to security admins for role-management actions (add_*).
- Read operations (pull, fork) remain allowed on archived repos.
- Issue operations are unaffected by archive status.

## Notes
- The archive forbid must use an `unless` clause for the security admin exception.
- This tests forbid/permit interaction with a carve-out.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Hard Mutations ────────────────────────────────────────────────────────────

class GitHubPRReviewWorkflow(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_pr_review_workflow",
            base_scenario="github",
            difficulty="hard",
            description="Add PullRequest + Review entities; merge requires approval, self-approval forbidden, archive blocks merge",
            operators=["S6", "S6", "S7", "S7", "S7", "P2", "P2", "P2", "P1", "P1"],
            features_tested=["multi_entity", "cross_traversal", "self_exclusion", "forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_entity(base_schema, """\
entity PullRequest = {
    repo: Repository,
    author: User,
};""")
        schema = schema_ops.add_entity(schema, """\
entity Review = {
    pullRequest: PullRequest,
    reviewer: User,
    approved: Bool,
};""")
        schema = schema_ops.add_action(schema, """\
// Pull request actions
action merge_pr appliesTo {
    principal: [User],
    resource: [PullRequest],
};

action approve_pr, request_changes appliesTo {
    principal: [User],
    resource: [PullRequest],
};""")
        spec = _BASE_SPEC + """\
### 7. Pull Request Permissions
- A **writer** (or above) of the PR's repository may **merge** the pull request.
- A **reader** (or above) of the PR's repository may **approve** or **request_changes** on the PR.
- The **author** of a pull request may NOT **approve** their own PR (self-approval forbidden).
- **Merging** is blocked on archived repositories (same as other write operations).

### 8. Review Entity
- Reviews belong to pull requests and have an `approved` boolean and `reviewer` reference.
- Reviews are informational for this policy — merge permissions are on PullRequest, not Review.

## Notes (PR Workflow)
- Three entity types interact: Issue, PullRequest, Review — all referencing Repository.
- Self-exclusion (`principal == resource.author`) creates a forbid rule on PullRequest.
- Archive blocking extends to merge_pr via the PullRequest → Repository traversal.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubFullExpansion(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_full_expansion",
            base_scenario="github",
            difficulty="hard",
            description="Add PullRequest, isPrivate, isLocked, Contributor role, close_issue; 5 mutations",
            operators=["S6", "S1", "S1", "S9", "S7", "P2", "P2", "P1", "P1"],
            features_tested=["multi_mutation", "complexity"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "isPrivate", "Bool")
        schema = schema_ops.add_attribute(schema, "Repository", "contributors", "UserGroup")
        schema = schema_ops.add_attribute(schema, "Issue", "isLocked", "Bool")
        schema = schema_ops.add_entity(schema, """\
entity PullRequest = {
    repo: Repository,
    author: User,
};""")
        schema = schema.replace(
            "action assign_issue, delete_issue, edit_issue appliesTo {",
            "action assign_issue, delete_issue, edit_issue, close_issue appliesTo {"
        )
        schema = schema_ops.add_action(schema, """\
// Pull request actions
action merge_pr, approve_pr appliesTo {
    principal: [User],
    resource: [PullRequest],
};""")
        spec = """\
# GitHub Repository Permissions — Policy Specification (Full Expansion)

## Context

This policy governs access control for a GitHub-like platform with
Organizations, Repositories, Issues, Pull Requests, Users, and Teams.

Repositories have six role tiers: readers, triagers, contributors, writers, maintainers, and admins.

## Requirements

### 1. Reader Permissions
- A **reader** may **pull** and **fork** a repository.
- A reader may **delete**, **edit**, or **close** an issue ONLY if they are the **reporter**.

### 2. Triager Permissions
- A **triager** may **assign** issues.

### 3. Contributor Permissions
- A **contributor** may **push** to a repository.
- Contributors may NOT edit or delete issues (unless they are the reporter and a reader).

### 4. Writer Permissions
- A **writer** may **push** to a repository.
- A writer may **edit** or **close** any issue.

### 5. Maintainer Permissions
- A **maintainer** may **delete** any issue.
- A maintainer may **merge** any pull request.

### 6. Admin Permissions
- An **admin** may add users to any role: add_reader, add_triager, add_writer, add_maintainer, add_admin.

### 7. Pull Request Permissions
- A **writer** (or above) may **merge** a pull request in the PR's repository.
- A **reader** (or above) may **approve** a pull request.
- The **author** of a PR may NOT approve their own PR.

### 8. Archived Repository Block (Deny Rule)
- If `isArchived == true`: forbid push, merge_pr, and all add_* actions.
- Read operations (pull, fork) and issue operations are unaffected.

### 9. Private Repository Restriction (Deny Rule)
- If `isPrivate == true`: forbid **fork**.

### 10. Locked Issue Block (Deny Rule)
- If `isLocked == true`: forbid **edit_issue**.
- delete_issue, close_issue, and assign_issue are still allowed.

## Notes
- This is a complex scenario with 6 roles, 3 forbid rules, and 2 entity types with cross-traversal.
- Three independent forbid rules operate on different entity types and block different actions.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class GitHubNumericConstraints(Mutation):
    def meta(self):
        return MutationMeta(
            id="github_numeric_constraints",
            base_scenario="github",
            difficulty="hard",
            description="Add maxCollaborators on Repo and accountAge on User; numeric threshold forbids",
            operators=["S2", "S2", "P1", "P1", "P10"],
            features_tested=["numeric_comparison", "multi_constraint"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = schema_ops.add_attribute(base_schema, "Repository", "collaboratorCount", "Long")
        schema = schema_ops.add_attribute(schema, "Repository", "maxCollaborators", "Long")
        schema = schema_ops.add_attribute(schema, "User", "accountAgeDays", "Long")
        # User needs an attributes block — currently just `entity User in [UserGroup, Team];`
        schema = schema.replace(
            "entity User in [UserGroup, Team];",
            "entity User in [UserGroup, Team] = {\n    accountAgeDays: Long,\n};"
        )
        # Remove the line we added via add_attribute since we did it manually
        schema = schema.replace(
            "    accountAgeDays: Long,\n    accountAgeDays: Long,",
            "    accountAgeDays: Long,"
        )
        spec = _BASE_SPEC + """\
### 7. Collaborator Limit (Deny Rule)
- If a repository's `collaboratorCount >= maxCollaborators`, forbid all **add_*** actions
  (add_reader, add_triager, add_writer, add_maintainer, add_admin).
- This is independent of the archive block — both may apply simultaneously.

### 8. New Account Restriction (Deny Rule)
- If a user's `accountAgeDays < 30`, forbid the **push** action.
- New accounts can still pull, fork, and work with issues — only push is restricted.

## Notes (Numeric Constraints)
- Numeric comparisons require precise operators: `>=` for the limit check, `<` for the age check.
- The collaborator limit uses two attributes on the same entity compared to each other.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# ── Registration ──────────────────────────────────────────────────────────────

MUTATIONS = [
    GitHubAddPrivate(),
    GitHubAddCloseIssue(),
    GitHubRemoveTriager(),
    GitHubAddLockedIssue(),
    GitHubNoArchive(),
    GitHubAddPullRequest(),
    GitHubAddContributor(),
    GitHubPrivateAndLocked(),
    GitHubAddVisibility(),
    GitHubAddSecurityAdmin(),
    GitHubPRReviewWorkflow(),
    GitHubFullExpansion(),
    GitHubNumericConstraints(),
]

for m in MUTATIONS:
    register(m)
