---
pattern: empty-set vacuous truth (default-deny on empty requirements)
difficulty: hard
features:
  - Set<String> attributes
  - ".containsAll()" with empty-set vacuous truth
  - ".isEmpty()" guard against vacuous-true trap
  - role-based bypass
domain: workplace safety / training compliance
synthesis_difficulty: 4
---

# Empty-Set Vacuous Truth — Policy Specification

## Context

A workstation access system where each `Workstation` lists a set of
`requiredTrainings` (e.g. "forklift", "lockout-tagout", "hazmat"), and
each `Employee` carries a set of `completedTrainings`. An employee may
operate a workstation when they have completed every required training.

This scenario specifically exercises a Cedar correctness trap:

> `[].containsAll(anything) == true` (vacuous truth).

A naive policy `permit when employee.completedTrainings.containsAll(workstation.requiredTrainings)`
permits ANY employee — including ones with zero completed trainings —
to operate ANY workstation whose requirements list is empty. In a
training-compliance domain this is a safety-critical bug: an empty
requirements list means "we have not configured this workstation yet,"
NOT "no training is required."

## Requirements

### 1. useWorkstation — Default-Deny on Empty Requirements

An `Employee` may `useWorkstation` on a `Workstation` when ALL of:
- The workstation's `requiredTrainings` set is **non-empty**
  (`!resource.requiredTrainings.isEmpty()`), AND
- The employee's `completedTrainings` set contains every required
  training (`principal.completedTrainings.containsAll(resource.requiredTrainings)`).

If `requiredTrainings` is empty, the workstation is treated as
unconfigured and access is **denied**. This is the safe default.

### 2. bypass — Admin-Only

An `Employee` may `bypass` a `Workstation` when:
- The employee has the `"admin"` role
  (`principal.role == "admin"`).

Bypass performs no training check. It exists for emergency maintenance
by trusted operations staff.

### 3. Default Deny

All other requests are denied. In particular:
- Non-admin employees cannot `bypass`.
- An employee cannot `useWorkstation` when ANY required training is
  missing from their completed set, OR when the requirements list is
  empty (unconfigured workstation).
