---
pattern: backup/restore asymmetric permissions
difficulty: medium
features:
  - asymmetric action permissions (backup easy, restore restricted)
  - role + boolean flag for restore authorization
  - environment-based restriction (production vs staging)
domain: infrastructure / DevOps
synthesis_difficulty: 2
---

# Backup/Restore Asymmetric — Policy Specification

## Context

A backup management system where `Operator` principals manage
`System` resources. Backup and restore have deliberately asymmetric
permission models: creating backups is routine, but restoring from a
backup is a high-risk operation that requires additional authorization.

Each System has an `environment` attribute (`"production"` or
`"staging"`). Each Operator has a `role` (`"engineer"`, `"sre"`,
`"admin"`) and an `isOnCall` boolean.

## Requirements

### 1. Backup — Engineers and Above
An Operator may `backup` a System when:
- The operator's role is `"engineer"`, `"sre"`, or `"admin"`.

Any authorized operator can create backups regardless of environment.

### 2. Restore to Staging — SRE and Admin
An Operator may `restore` a System when:
- The system's environment is `"staging"`, AND
- The operator's role is `"sre"` or `"admin"`.

### 3. Restore to Production — Admin or On-Call SRE
An Operator may `restore` a System when:
- The system's environment is `"production"`, AND
- The operator's role is `"admin"`, OR
- The operator's role is `"sre"` AND `principal.isOnCall == true`.

Production restores require either admin privilege or active on-call
status. An off-call SRE cannot restore to production.

### 4. Verify — Any Operator
An Operator may `verify` a System's backup integrity when:
- The operator's role is `"engineer"`, `"sre"`, or `"admin"`.

### 5. Default Deny
All other requests are denied. Notably, engineers cannot restore
to any environment.
