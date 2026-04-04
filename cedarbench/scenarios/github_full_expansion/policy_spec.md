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
