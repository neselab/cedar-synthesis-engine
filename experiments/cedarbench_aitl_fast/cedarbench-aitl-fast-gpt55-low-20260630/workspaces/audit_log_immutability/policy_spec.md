---
pattern: audit log immutability (append-only)
difficulty: medium
features:
  - asymmetric action permissions (append always, delete never)
  - role hierarchy with compliance override for read
  - forbid rule for unconditional delete denial
domain: compliance / SOX
synthesis_difficulty: 2
---

# Audit Log Immutability — Policy Specification

## Context

An audit logging system where `AuditEntry` records are append-only.
Once written, they cannot be modified or deleted — this is a
fundamental compliance requirement (SOX, HIPAA, PCI-DSS).

Users have roles: `"service"` (application services that write logs),
`"analyst"` (reads logs for investigation), `"auditor"` (reads logs
for compliance review), `"admin"` (system administration).

## Requirements

### 1. Append — Services Only
A User may `append` an AuditEntry when:
- The user's role is `"service"`.

Only application services can write new audit entries.

### 2. Read — Analysts, Auditors, and Admins
A User may `read` an AuditEntry when:
- The user's role is `"analyst"` or `"auditor"` or `"admin"`.

Services do NOT have read access to audit logs (write-only).

### 3. Export — Auditors Only
A User may `export` an AuditEntry when:
- The user's role is `"auditor"`.

Exporting bulk audit data is restricted to the compliance function.

### 4. Delete — FORBIDDEN FOR ALL ROLES
No User may `delete` an AuditEntry, regardless of role. This is the
immutability guarantee. Even admins cannot delete audit entries.

This must be an unconditional deny.

### 5. Modify — FORBIDDEN FOR ALL ROLES
No User may `modify` an AuditEntry, regardless of role. Audit entries
are immutable once written.

### 6. Default Deny
All other requests are denied.
