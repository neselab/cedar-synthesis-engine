---
pattern: counterintuitive role / read-only auditor admin
difficulty: hard (RBAC prior resistance)
features:
  - role-based access on string attribute
  - counterintuitive privilege asymmetry
  - read-broadest / write-narrowest role
domain: audit / compliance / oversight
synthesis_difficulty: 4
---

# Read-Only Auditor Admin — Policy Specification

## Context

This policy governs access to operational `Record` resources by `Worker`
principals. The deployment supports three roles, encoded as the string
attribute `Worker.role`:

- `editor` — operational staff who view and edit records.
- `manager` — supervisors who view, edit, and delete records.
- `auditAdmin` — oversight role with broad VIEW access for transparency,
  but ZERO write power.

For audit transparency, the `auditAdmin` role can view ALL records but
is FORBIDDEN from editing or deleting. The `auditAdmin` role exists
specifically to provide oversight without operational power. Even
though `auditAdmin` is the most privileged role for VIEW, it has ZERO
write permissions. This is the entire point of the role: an auditor
who can also mutate the records they audit is not an independent
auditor.

This is counterintuitive: in conventional RBAC mental models, an "admin"
role is assumed to be a superset of every other role's permissions. Here,
that assumption is wrong. A naive synthesizer that follows the prior
"admin = can do everything" will produce an over-permissive policy.

## Requirements

### 1. View Access (`view`)
- Permit `view` when `principal.role == "editor"`.
- Permit `view` when `principal.role == "manager"`.
- Permit `view` when `principal.role == "auditAdmin"`.
- (i.e., all three roles may view.)

### 2. Edit Access (`edit`)
- Permit `edit` when `principal.role == "editor"`.
- Permit `edit` when `principal.role == "manager"`.
- The `auditAdmin` role MUST NOT be able to `edit`. Auditors observe;
  they do not modify.

### 3. Delete Access (`delete`)
- Permit `delete` when `principal.role == "manager"`.
- Neither `editor` nor `auditAdmin` may `delete`. Deletion is reserved
  for managers only.

## Notes

- Per §8.6, the auditAdmin write-prohibition is encoded **positively**:
  the `edit` and `delete` permits simply do not enumerate `auditAdmin`.
  Do NOT introduce a `forbid when principal.role == "auditAdmin"` policy:
  Cedar role attributes are scalars in this schema (a single string), so
  the §8.6 role-intersection trap does not apply mechanically — but the
  positive-permit form is the project's standing convention and makes the
  bound structure obvious.
- The roles are mutually exclusive at the value level (`role` is a single
  string), but the policy author should still write the rules without
  relying on that mutual-exclusivity for soundness; each permit guards
  its own role explicitly.
- Liveness: each of the three actions must be permittable for SOME
  principal/resource pair, so all three actions get a liveness check.
