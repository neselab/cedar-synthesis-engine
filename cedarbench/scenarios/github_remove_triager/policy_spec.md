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
