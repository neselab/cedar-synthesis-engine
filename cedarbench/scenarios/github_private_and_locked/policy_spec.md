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
### 7. Private Repository Restriction (Deny Rule)
- If a repository is private (`isPrivate == true`), the **fork** action is forbidden.
- All other actions are unaffected by the private flag.

### 8. Locked Issue Block (Deny Rule)
- If an issue is locked (`isLocked == true`), the **edit_issue** action is forbidden for all users.
- **delete_issue** and **assign_issue** are still allowed on locked issues.

## Notes (Multiple Forbid Rules)
- This scenario has THREE independent forbid rules: archive block, private block, and locked block.
- Each forbid operates on a different entity type and blocks different actions.
