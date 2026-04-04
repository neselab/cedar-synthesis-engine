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
