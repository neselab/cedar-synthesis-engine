---
pattern: customer support ticket escalation
difficulty: medium
features:
  - priority-based access gating (Long comparison)
  - boolean flag gating (isEscalated)
  - role-based action restriction (manager-only reassign)
  - universally permitted action (escalate)
domain: customer support
synthesis_difficulty: 3
---

# Customer Support Ticket Escalation -- Policy Specification

## Context

This policy governs a customer support ticket system where agents are
organized by tier (tier1 through tier3, plus manager). Each agent has
a `maxPriority` attribute (1--4) indicating the highest priority ticket
they are authorized to handle. Tickets have a numeric `priority`
(1 = low, 4 = critical) and a boolean `isEscalated` flag.

The system enforces priority-based routing so that agents only work on
tickets within their competence level. Escalated tickets receive
special handling: only managers can close them.

## Requirements

### 1. Respond -- Priority Gating

- **Permit** `respond` when the agent's `maxPriority` is greater than
  or equal to the ticket's `priority`.
- An agent with `maxPriority == 2` can respond to priority-1 and
  priority-2 tickets, but NOT priority-3 or priority-4 tickets.

### 2. Escalate -- Universally Permitted

- **Permit** `escalate` for any agent on any ticket, unconditionally.
- Rationale: any agent who notices a ticket needs higher-tier
  attention should be able to escalate it immediately.

### 3. Close -- Priority Gating Plus Escalation Guard

- **Permit** `close` when the agent's `maxPriority` is greater than or
  equal to the ticket's `priority` AND the ticket is NOT escalated
  (`resource.isEscalated == false`).
- Escalated tickets can only be closed by a manager. This is the key
  safety property: a tier-2 agent cannot close a priority-2 escalated
  ticket even though they meet the priority requirement.
- Managers (`role == "manager"`) can close any ticket including
  escalated ones, subject to the priority gate.

### 4. Reassign -- Manager Only

- **Permit** `reassign` only when the agent's role is `"manager"`.
- No priority gate: managers can reassign any ticket regardless of
  priority or escalation status.

## Notes

- The priority comparison `principal.maxPriority >= resource.priority`
  is a numeric (Long) comparison, not a string comparison.
- The close rule composes two conditions: priority gating AND
  non-escalation (for non-managers). Per section 8.8 of the harness fix
  log, floor references for close must include the `!resource.isEscalated`
  condition so they remain satisfiable alongside the ceiling.
- There is no global forbid in this scenario. The deny-by-default
  semantics of Cedar handle unauthorized access: if no permit matches,
  the request is denied.
- Common failure modes: (a) forgetting the escalation guard on close,
  (b) adding a priority gate to escalate, (c) adding a priority gate
  to reassign, (d) using string comparison instead of Long comparison
  for priority.
