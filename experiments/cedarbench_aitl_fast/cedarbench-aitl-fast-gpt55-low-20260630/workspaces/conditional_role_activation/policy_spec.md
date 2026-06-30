---
pattern: conditional role activation
difficulty: medium
features:
  - context attestation
  - principal attribute gating
  - geo-fenced role activation
  - role conditional on environment
domain: enterprise security
synthesis_difficulty: 2
---

# Conditional Role Activation — Policy Specification

## Context

This policy implements **geo-fenced role activation** for an enterprise
secure system. An employee's `homeRole` attribute names the role they
have been provisioned with (`"user"` or `"admin"`), but the elevated
`"admin"` role is only "active" when the employee is connecting from
the office network AND has an explicit office-network authorization
flag set on their account. Outside that environment the elevated role
collapses back to ordinary read-only access.

Principal is `Employee`; resource is `SecureSystem`.

## Requirements

### 1. Read Access (Baseline)
- Any `Employee` may perform `read` on a `SecureSystem`. There are no
  network or role restrictions on read.

### 2. Admin Configuration (Geo-Fenced + Provisioned)
- An `Employee` may perform `adminConfig` on a `SecureSystem` ONLY when
  ALL of the following hold:
  - `principal.homeRole == "admin"` (the employee was provisioned
    with the admin role), AND
  - `context.connectedFromOffice == true` (the request is coming from
    the office network, attested by the network gateway in context), AND
  - `principal.officeNetworkAuth == true` (the employee's account has
    the office-network authorization flag set — a separate provisioning
    step from being in the admin role).
- All three conditions are required. Any one missing must result in a
  deny. In particular:
  - An admin connecting from outside the office cannot adminConfig.
  - An admin missing the `officeNetworkAuth` provision cannot adminConfig
    even from the office.
  - A non-admin (`homeRole != "admin"`) cannot adminConfig under any
    circumstance.

## Notes
- The `now` context attribute is included in the schema for parity with
  other realworld scenarios but is not load-bearing for this policy.
- Common failure modes to avoid: (a) treating `homeRole == "admin"`
  alone as sufficient for adminConfig, (b) forgetting the
  `officeNetworkAuth` gate, (c) restricting `read` to office-network
  only.
