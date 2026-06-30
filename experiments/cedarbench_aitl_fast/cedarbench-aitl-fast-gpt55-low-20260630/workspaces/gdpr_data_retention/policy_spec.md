---
pattern: GDPR data retention + right-to-erasure
difficulty: hard
features:
  - datetime comparison for retention period expiry
  - boolean flag for erasure request
  - role-based access with compliance override
  - action-specific temporal constraints
domain: compliance / GDPR
synthesis_difficulty: 3
---

# GDPR Data Retention — Policy Specification

## Context

A data platform that stores personal data records (`DataRecord`) with a
`retentionExpiry` datetime and an `erasureRequested` boolean flag. Users
have roles: `"processor"` (handles data), `"controller"` (manages data
lifecycle), `"dpo"` (Data Protection Officer — compliance oversight).

The policy enforces GDPR-style data retention and right-to-erasure rules.

## Requirements

### 1. Read Access — Active Records Only
A User may `read` a DataRecord when:
- The record's retention period has NOT expired
  (`resource.retentionExpiry > context.now`), AND
- The record has NOT been flagged for erasure
  (`resource.erasureRequested == false`), AND
- The user's role is `"processor"` or `"controller"` or `"dpo"`.

### 2. Process Access — Processors on Active Records
A User may `process` a DataRecord when:
- The user's role is `"processor"`, AND
- The record's retention period has NOT expired, AND
- The record has NOT been flagged for erasure.

### 3. Delete Access — Controllers or DPO Only
A User may `delete` a DataRecord when:
- The user's role is `"controller"` or `"dpo"`.

Deletion is allowed regardless of retention or erasure status — a
controller must be able to delete records that are expired or flagged
for erasure.

### 4. Audit Access — DPO Compliance Override
A User may `audit` a DataRecord when:
- The user's role is `"dpo"`.

The DPO can audit ANY record regardless of retention expiry or erasure
status. This is the compliance override — the DPO needs to verify that
erasure was completed and retention policies are being followed.

### 5. Default Deny
All other requests are denied. Notably:
- Processors cannot read or process expired or erasure-flagged records.
- No role can `process` an expired record.
- Only controllers and DPOs can delete.
