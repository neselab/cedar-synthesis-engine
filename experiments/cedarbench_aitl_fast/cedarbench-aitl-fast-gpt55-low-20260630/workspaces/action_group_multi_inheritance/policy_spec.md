---
pattern: action_group_multi_inheritance
difficulty: medium
features:
  - action groups
  - multi-parent action inheritance
  - cross-cutting capability requirements
  - forbid-based gating
domain: document_management
synthesis_difficulty: 3
---

# DocumentVault — Action Groups With Multi-Parent Inheritance

## System

DocumentVault uses Cedar **action groups** to express orthogonal,
cross-cutting capability requirements. Concrete actions inherit from
multiple action groups simultaneously, and each parent group encodes
an independent requirement that must hold whenever the concrete action
is invoked.

## Entities

- `User { role: String, auditCleared: Bool }`
  - `role` is one of `"member"`, `"admin"`.
  - `auditCleared` indicates the user has signed the audit-log retention
    policy (a compliance prerequisite for any action whose invocation is
    written to the immutable audit log).
- `Document` — opaque resource, no attributes.

## Action groups

There are three action groups. Each group encodes an orthogonal
capability requirement. Concrete actions belong to one or more groups
to declare which requirements apply.

- `ReadOnly` — actions in this group do not mutate the document.
  ReadOnly imposes no additional principal requirement on its own
  (any authenticated user may perform a read).
- `AuditLogged` — actions in this group are recorded in the audit log.
  Performing any AuditLogged action requires `principal.auditCleared`.
- `Destructive` — actions in this group destroy or remove data.
  Performing any Destructive action requires `principal.role == "admin"`.

## Concrete actions

| Action  | Parent groups               |
|---------|-----------------------------|
| `View`  | `ReadOnly`, `AuditLogged`   |
| `Search`| `ReadOnly`                  |
| `Edit`  | `AuditLogged`               |
| `Delete`| `AuditLogged`, `Destructive`|

## Authorization rules (semantics)

A request is permitted iff:

1. The action belongs to one of the four concrete actions above
   (`View`, `Search`, `Edit`, `Delete`), AND
2. **Every** group requirement attached to the action's parent groups
   is satisfied.

Concretely:

- `Search` (ReadOnly only) — permitted for any user.
- `View` (ReadOnly + AuditLogged) — permitted iff `principal.auditCleared`.
- `Edit` (AuditLogged only) — permitted iff `principal.auditCleared`.
- `Delete` (AuditLogged + Destructive) — permitted iff
  `principal.auditCleared && principal.role == "admin"`.

If any requirement of any parent group is unmet, the request is denied.
There is no "OR" across groups: the requirements compose by conjunction.

## Liveness

There exists at least one permitted request for each of the four
concrete actions:

- A user may `Search` any document (no preconditions).
- An audit-cleared user may `View` any document.
- An audit-cleared user may `Edit` any document.
- An audit-cleared admin may `Delete` any document.
