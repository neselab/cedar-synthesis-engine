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
