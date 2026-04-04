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
