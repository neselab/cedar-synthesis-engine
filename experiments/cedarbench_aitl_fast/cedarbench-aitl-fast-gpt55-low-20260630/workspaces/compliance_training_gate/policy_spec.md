---
pattern: compliance training gate
difficulty: medium
features:
  - containsAll set operation
  - boolean gate (isSensitive)
  - role-based action restriction
  - compositional permit conditions
domain: compliance/enterprise
synthesis_difficulty: 2
---

# Compliance Training Gate -- Policy Specification

## Context

This policy governs access to enterprise systems where employees must
complete all required compliance trainings before they are allowed to
interact with a system. Each system declares a set of required training
course IDs, and each employee has a set of completed training course IDs.
Access is granted only when the employee's completed set fully covers the
system's required set (`containsAll`).

Three actions exist: `access` (general use), `export` (data export), and
`adminConfig` (administrative configuration). Each has progressively
stricter requirements.

## Requirements

### 1. Access -- Training Gate (Permit)
- An Employee may `access` a System when the employee's
  `completedTrainings` contains ALL of the system's `requiredTrainings`:
  `principal.completedTrainings.containsAll(resource.requiredTrainings)`.
- No role restriction applies to this action; any employee who has
  completed the required trainings may access the system.

### 2. Export -- Training Gate + Non-Sensitive (Permit)
- An Employee may `export` from a System when BOTH:
  - The training gate is satisfied:
    `principal.completedTrainings.containsAll(resource.requiredTrainings)`,
    AND
  - The system is NOT marked as sensitive: `!resource.isSensitive`.
- Sensitive systems (`resource.isSensitive == true`) can NEVER be
  exported, regardless of training completion or role.

### 3. AdminConfig -- Manager + Training Gate (Permit)
- An Employee may `adminConfig` a System when BOTH:
  - The employee's role is `"manager"`:
    `principal.role == "manager"`, AND
  - The training gate is satisfied:
    `principal.completedTrainings.containsAll(resource.requiredTrainings)`.
- Non-manager employees (analysts, engineers) may never perform
  `adminConfig`, even if they have completed all trainings.

## Notes
- There are no explicit forbids in this scenario. Cedar's default-deny
  semantics mean that any request not matched by a permit is denied.
- The `isSensitive` flag is a hard block for export only. It does not
  affect `access` or `adminConfig`.
- The training gate is the common condition across all three actions.
  The export action adds the sensitivity check; the adminConfig action
  adds the role check.
- Common pitfalls: forgetting the `containsAll` direction (it is the
  employee's set that must contain the system's set, not the reverse),
  allowing export on sensitive systems, or allowing non-managers to
  perform adminConfig.
