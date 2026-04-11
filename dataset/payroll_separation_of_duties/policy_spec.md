---
pattern: separation of duties (SoD / mutual exclusion)
difficulty: medium
features:
  - same-person-forbid across actions on the same resource
  - role-based action assignment
  - amount-thresholded escalation (CFO-only for large entries)
domain: finance / SOX compliance
---

# Payroll Separation of Duties — Policy Specification

## Context

This policy implements the classic Separation of Duties (SoD) pattern
required by SOX and similar financial controls. A `PayrollEntry`
represents a pending payroll transaction. It moves through the states
`"draft"` → `"pending_approval"` → `"approved"` → `"released"`, with
a possible `"rejected"` terminal state. The central safety property:
**the user who initiates an entry may not also approve it**. Approval
and initiation must be performed by different people.

Principal is `User`; resource is `PayrollEntry`. Users have a `role`
attribute which is one of `"clerk"`, `"manager"`, or `"cfo"`. Five
actions: `initiate`, `approve`, `release`, `reject`, `read`.

## Requirements

### 1. Initiate (Clerk Only, Draft Only)
- A `clerk` may `initiate` a PayrollEntry when its status is `"draft"`.
  This transitions the entry to `"pending_approval"` and sets the
  `initiator` attribute to the acting clerk.
- Managers and CFOs are NOT permitted to initiate entries — this is
  deliberate and ensures that the initiator is always at a lower
  authority tier than the approver.
- Concretely: permit `initiate` when `principal.role == "clerk"`
  AND `resource.status == "draft"`.

### 2. Approve (Manager or CFO, Not Initiator)
- A `manager` or `cfo` may `approve` a PayrollEntry when its status is
  `"pending_approval"`, PROVIDED they are NOT the user who initiated
  the entry (`principal != resource.initiator`). This is the core SoD
  check.
- A clerk cannot approve under any circumstance, regardless of whether
  they initiated the entry.
- Concretely: permit `approve` when:
  - `principal.role == "manager"` OR `principal.role == "cfo"`, AND
  - `resource.status == "pending_approval"`, AND
  - `principal != resource.initiator`.

### 3. Large-Entry Escalation (CFO-Only Approval Above $50,000)
- For entries with `amount >= 50000`, approval requires a CFO
  specifically — manager approval is insufficient.
- Concretely: **forbid** `approve` when ALL of:
  - `resource.amount >= 50000`, AND
  - `principal.role != "cfo"`.
- This forbid overrides the §2 manager-approval permit for large
  entries.

### 4. Release (CFO Only, Approved Entries)
- Only a `cfo` may `release` a PayrollEntry, and only when the entry
  is in `"approved"` status.
- Concretely: permit `release` when `principal.role == "cfo"` AND
  `resource.status == "approved"`.

### 5. Reject (Manager or CFO, Pending)
- A `manager` or `cfo` may `reject` a PayrollEntry in `"pending_approval"`
  status, regardless of initiator (rejection is not subject to the SoD
  check — you can reject your own entries to cancel them).
- Concretely: permit `reject` when (`principal.role == "manager"` OR
  `principal.role == "cfo"`) AND `resource.status == "pending_approval"`.

### 6. Read (All Roles)
- Any User may `read` any PayrollEntry regardless of role, status, or
  relation to the entry. This is a transparency requirement.
- Concretely: permit `read` unconditionally.

### 7. No Actions on Terminal States (Forbid)
- Once a PayrollEntry is in `"released"` or `"rejected"` state, no
  further `initiate`, `approve`, `release`, or `reject` actions may
  be performed on it. `read` is still allowed.
- Concretely: **forbid** `initiate`, `approve`, `release`, or `reject`
  when `resource.status == "released"` OR `resource.status == "rejected"`.

## Notes
- The key SoD property is the `principal != resource.initiator` check
  on the approve permit. Common failure modes: (a) forgetting this
  check entirely, (b) checking it only for managers and not CFOs,
  (c) checking `principal.role != resource.initiator.role` instead
  of the principal identity.
- The large-entry escalation is a forbid with a role predicate. The
  base manager-approval permit remains — the forbid just fires for
  entries above the threshold to knock manager approval out.
- Cedar supports `Long` comparisons natively, so `resource.amount >=
  50000` works without any conversion.
