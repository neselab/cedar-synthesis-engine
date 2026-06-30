---
pattern: tiered incident escalation access
difficulty: hard
features:
  - severity-to-clearance level mapping (sev1->3, sev2->2, sev3->1)
  - role-based tiering (oncall < lead < commander)
  - active vs resolved incident distinction
  - post-mortem log access survives resolution
domain: security/SRE
synthesis_difficulty: 3
---

# Incident Response War Room

## Context

An incident-response platform controls who can interact with active
incidents based on their responder role and numeric clearance level.
The system enforces tiered escalation: higher-severity incidents require
higher clearance to modify, while basic visibility is broad. Post-mortem
log access is intentionally kept open to senior responders even after
an incident is resolved.

Responders have a `role` string (`"oncall"`, `"lead"`, `"commander"`)
and a `clearanceLevel` long (1-3). Incidents have a `severity` string
(`"sev1"`, `"sev2"`, `"sev3"`) and an `isActive` boolean.

## Requirements

### Action: viewDetails

Any responder may view details of an **active** incident regardless of
role or clearance level.

Ceiling: permit only when `resource.isActive == true`.

Floor: any responder MUST be permitted to view an active incident.

### Action: updateStatus

A responder may update the status of an **active** incident when their
clearance level meets or exceeds the threshold for the incident's
severity:

- `sev1` requires `clearanceLevel >= 3`
- `sev2` requires `clearanceLevel >= 2`
- `sev3` requires `clearanceLevel >= 1`

Ceiling: permit only when `resource.isActive == true` AND the
clearance-severity mapping is satisfied.

Floor: a responder with clearance level 3 MUST be permitted to update
status on an active sev1 incident.

Floor: a responder with clearance level 2 MUST be permitted to update
status on an active sev2 incident.

### Action: accessLogs

Only responders with role `"lead"` or `"commander"` may access incident
logs. This applies to **any** incident, including resolved ones, to
support post-mortem analysis.

Ceiling: permit only when `principal.role == "lead" || principal.role == "commander"`.

Floor: a lead MUST be permitted to access logs on any incident
(regardless of active/resolved state).

### Action: declareResolved

Only responders with role `"commander"` may declare an incident
resolved. The incident must be **active**.

Ceiling: permit only when `principal.role == "commander"` AND
`resource.isActive == true`.

Floor: a commander MUST be permitted to declare an active incident
resolved.

### Liveness

Each of the four actions must permit at least one request. No action
should end up globally denied.

## Out of scope

- No global forbids.
- No temporal constraints (on-call windows, shift schedules).
- No incident ownership or assignment; access is role- and
  clearance-based only.
- No entity group hierarchy for roles -- roles are modeled as string
  attributes to exercise the clearance-mapping logic.
