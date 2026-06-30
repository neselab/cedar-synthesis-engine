---
pattern: multi-level namespace organization
difficulty: medium
features:
  - three-level namespace (`Company::Billing::Invoice`)
  - cross-namespace entity type references
  - qualified principal/action/resource types in rule heads
domain: enterprise SaaS / billing
synthesis_difficulty: 2
---

# Nested Namespaces — Billing Invoice Lines

## Context

This scenario exercises Cedar's multi-level namespace organization. Two
namespaces are involved:

- `Company::Identity` — defines `Employee` and `Team`. Employees have
  a `department` string and a `level` long (1 = junior, 5 = senior,
  6+ = executive). Teams have a `manager` who is an `Employee`.
- `Company::Billing::Invoice` — defines `Line` (an invoice line-item)
  and three actions (`view`, `approve`, `void`). Lines reference
  employees and teams from the other namespace: an issuer (who filed
  the line) and an owning team.

The policy controls who can act on invoice lines. Every principal is a
`Company::Identity::Employee`; every resource is a
`Company::Billing::Invoice::Line`. Actions are qualified
`Company::Billing::Invoice::Action::"..."`.

## Requirements

### Action: view

A Line may be viewed when any of the following hold:

1. The principal is the issuer: `principal == resource.issuer`.
2. The principal is the owning team's manager:
   `principal == resource.owningTeam.manager`.
3. The principal is in the same department as the issuer:
   `principal.department == resource.issuer.department`.

Floors:
- The issuer MUST always be permitted to view their own line.
- The owning team's manager MUST always be permitted to view.

### Action: approve

A Line may be approved when ALL of the following hold for one of the
two approval tiers:

- **Tier 1 (team-level approval, small amounts):**
  - The principal is the owning team's manager, AND
  - The principal's level is at least 3, AND
  - The line total is at most 10000.

- **Tier 2 (executive approval, large amounts):**
  - The principal's level is at least 5, AND
  - The line total is at most 100000.

Floor:
- A team manager with level 3 or higher MUST be permitted to approve a
  line with total ≤ 10000 on their own team.

### Action: void

A Line may be voided when ALL of the following hold:

- The principal is the owning team's manager, AND
- The principal's level is at least 5 (senior or executive).

This is an irreversible action; deliberately restrictive.

Floor:
- A level-5 or higher team manager MUST be permitted to void a line on
  their own team.

### Liveness

Each of the three actions must permit at least one request. (No
action should end up globally denied.)

## Out of scope

- No temporal constraints (expiry, business hours).
- No role concept beyond the numeric `level`.
- No cross-team delegation.
- No global forbids.
