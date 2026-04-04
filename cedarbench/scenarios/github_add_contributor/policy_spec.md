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
