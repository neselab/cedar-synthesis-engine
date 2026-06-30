---
pattern: hierarchical role inheritance with per-level override
difficulty: medium
features:
  - 3-level role hierarchy via numeric level attribute
  - per-level exception override (senior cannot execute restricted)
  - per-(level, category) cell encoding to avoid §8.6 role-intersection trap
  - resource categorization gating
domain: enterprise access control
synthesis_difficulty: 3
---

# Hierarchical Role Override (Three Levels)

## Context

This policy governs access to resources of varying sensitivity by
employees at three hierarchical seniority levels. The naive design
("senior inherits junior, lead inherits senior") collides with a
business rule: **senior employees may VIEW restricted actions but may
not EXECUTE them**. Only leads have execute authority on restricted
resources. This is a real pattern in regulated industries: a senior
operator may need to inspect a high-impact configuration to diagnose
issues, but only a lead may actually trigger it.

Every `Employee` has a numeric `level` attribute (1=junior, 2=senior,
3=lead). Every `Resource` has a `category` attribute, one of
`"standard"`, `"criticalAction"`, or `"restrictedAction"`.

Two actions: `read` and `execute`.

## Requirements

The full access matrix is:

| Level         | standard read | standard execute | critical read | critical execute | restricted read | restricted execute |
| ------------- | ------------- | ---------------- | ------------- | ---------------- | --------------- | ------------------ |
| 1 (junior)    | YES           | YES              | NO            | NO               | NO              | NO                 |
| 2 (senior)    | YES           | YES              | YES           | YES              | YES             | **NO (override)**  |
| 3 (lead)      | YES           | YES              | YES           | YES              | YES             | YES                |

Equivalent permit-cell enumeration (the encoding the policy MUST use,
to avoid the §8.6 role-intersection trap):

### 1. Read (Permit)

A User may `read` a Resource when ANY of:

- `principal.level >= 1 && resource.category == "standard"`
- `principal.level >= 2 && resource.category == "criticalAction"`
- `principal.level >= 2 && resource.category == "restrictedAction"`

(Read on `restrictedAction` requires senior or lead. Read on
`criticalAction` requires senior or lead. Read on `standard` is open
to any employee level >= 1.)

### 2. Execute (Permit)

A User may `execute` a Resource when ANY of:

- `principal.level >= 1 && resource.category == "standard"`
- `principal.level >= 2 && resource.category == "criticalAction"`
- `principal.level >= 3 && resource.category == "restrictedAction"`

(Note the asymmetry: execute on `restrictedAction` requires lead
specifically. This is the override: a senior who can READ a
restrictedAction resource still cannot EXECUTE it.)

## Notes

- Cedar denies by default. There are no global forbid rules; the
  bounds are purely positive permit cells.
- Encode each (level-floor, category) pair as its own permit clause
  (or as one permit with a disjunction of equivalent conditions).
  Do NOT encode "junior cannot execute restricted" as a forbid keyed
  on `principal.level == 1`, because §8.6 (role-intersection trap)
  warns against negative role-keyed forbids; the safe pattern here is
  cell-positive permits over a `>=` numeric threshold.
- The `level` attribute is required (not optional), so no `has`
  guard is needed.
- Common pitfalls: encoding the override as a forbid keyed on
  `principal.level == 2 && resource.category == "restrictedAction"`
  while also writing a "senior inherits all" permit — Cedar's
  evaluation will deny correctly but the policy is not minimal and
  may break under refactoring. Prefer positive cells.
