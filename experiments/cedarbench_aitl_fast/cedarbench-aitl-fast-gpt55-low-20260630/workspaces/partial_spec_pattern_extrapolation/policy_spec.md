---
pattern: partial spec with role-pattern extrapolation
difficulty: hard (planning)
features:
  - role-string discrimination
  - implicit permission inheritance
  - extrapolation from partial spec
  - per-role floors
domain: developer tools / source control
synthesis_difficulty: 3
---

# Partial Spec Pattern Extrapolation -- Policy Specification

## Context

This policy governs Developer access to CodeArtifact resources in a
source-control system. Each Developer carries a `role` string and an
`assignedProject` string; each CodeArtifact carries a `project` string.
Three roles exist in the system: `junior_dev`, `senior_dev`, and
`lead_dev`. Five actions exist: `read`, `write`, `review`, `merge`,
and `manageBranches`.

The planning challenge: the spec below describes the `junior_dev` and
`senior_dev` roles in full detail, but describes the `lead_dev` role
only by its delta against `senior_dev`. The planner must extrapolate
the full `lead_dev` permission set from the inheritance statement
("lead_dev extends senior_dev"). Concretely, this means:

- `lead_dev` inherits ALL `senior_dev` permissions
  (read/write any project, review any project).
- `lead_dev` ADDITIONALLY can merge pull requests and manage branches.

Roles other than the three named (`junior_dev`, `senior_dev`,
`lead_dev`) have no permissions in this system. Cedar denies by
default, so this is enforced implicitly.

## Requirements

### 1. junior_dev (described fully)

A Developer whose `role == "junior_dev"` MAY:
- `read` a CodeArtifact whose `project == principal.assignedProject`.
- `write` a CodeArtifact whose `project == principal.assignedProject`.

A junior_dev MAY NOT perform `review`, `merge`, or `manageBranches` on
any CodeArtifact, and MAY NOT read or write artifacts outside their
`assignedProject`.

### 2. senior_dev (described fully)

A Developer whose `role == "senior_dev"` MAY:
- `read` ANY CodeArtifact (project does not need to match).
- `write` ANY CodeArtifact (project does not need to match).
- `review` ANY CodeArtifact.

A senior_dev MAY NOT perform `merge` or `manageBranches` on any
CodeArtifact.

### 3. lead_dev (described as a delta)

The `lead_dev` role extends `senior_dev` with additional permissions
for merging pull requests and managing branches. Spelled out, this
means a Developer whose `role == "lead_dev"` MAY:
- everything a senior_dev may do, AND
- `merge` ANY CodeArtifact, AND
- `manageBranches` on ANY CodeArtifact.

### 4. Unrecognized roles

Any Developer whose `role` is not one of `"junior_dev"`, `"senior_dev"`,
or `"lead_dev"` has no permissions on any CodeArtifact under any
action. Cedar's default-deny posture handles this without any explicit
forbid.

## Notes

- The `assignedProject` field is present on every Developer but only
  meaningful for `junior_dev`. For `senior_dev` and `lead_dev` it is
  ignored by the policy.
- There are no per-resource owners, no time windows, no MFA, no
  delegation. Only role-string + project-string equality.
- The `review` action is meaningful only for senior_dev and lead_dev;
  the junior_dev floor / ceiling makes no claim about it.
- The floors below assert the *positive* lead_dev permissions
  explicitly so the planner cannot satisfy them by simply copying the
  senior_dev section and forgetting the merge / manageBranches
  extrapolation.
