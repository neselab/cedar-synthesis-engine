---
pattern: multi-factor resource unlock
difficulty: hard
features:
  - multiple boolean context attestations
  - role + context conjunction
  - graduated unlock levels
domain: security / vault
synthesis_difficulty: 3
---

# Multi-Factor Resource Unlock — Policy Specification

## Context

This policy implements a **graduated multi-factor unlock** scheme for a
secrets vault. Sensitive resources (secrets) are assigned a sensitivity
level (1 = low, 2 = medium, 3 = high). Higher-sensitivity secrets
require progressively more attestation factors before access is granted.
Factors are boolean context attributes representing out-of-band
verifications performed by the authentication layer before the
authorization request reaches Cedar.

Principals are `User` entities with a `role` attribute. Resources are
`Secret` entities with a `sensitivityLevel` attribute. Three actions
exist: `view`, `rotate`, and `revoke`, each with distinct role and
factor requirements.

## Entities

- **User** — `role: String` — one of `"operator"`, `"security_officer"`,
  or `"admin"`.
- **Secret** — `sensitivityLevel: Long` — `1` (low), `2` (medium), or
  `3` (high).

## Context attributes

All three are boolean flags injected by the authentication gateway:

| Attribute             | Meaning                                      |
|-----------------------|----------------------------------------------|
| `hasMfa`              | User completed a second-factor challenge.    |
| `hasManagerApproval`  | A manager approved this specific request.    |
| `hasSecurityReview`   | Security team reviewed and cleared request.  |

## Access rules

### 1. View

Any role may view a secret. The factor requirements scale with
sensitivity level:

| Level | Factors required            |
|-------|-----------------------------|
| 1     | None                        |
| 2     | `hasMfa`                    |
| 3     | `hasMfa` AND `hasManagerApproval` |

### 2. Rotate

Only `security_officer` or `admin` may rotate a secret. Factor
requirements:

| Level | Factors required                  |
|-------|-----------------------------------|
| 1     | `hasMfa`                          |
| 2     | `hasMfa`                          |
| 3     | `hasMfa` AND `hasSecurityReview`  |

### 3. Revoke

Only `admin` may revoke a secret. Regardless of sensitivity level,
revocation always requires `hasMfa` AND `hasManagerApproval`.

## Notes

- The three context booleans are independent attestations — they are
  not hierarchical (having `hasSecurityReview` does not imply `hasMfa`).
- The graduated structure is the core complexity: a candidate that
  applies uniform factor requirements across all levels will either
  be too permissive (failing a ceiling) or too restrictive (failing a
  floor).
- Common failure modes: (a) forgetting to gate level-2 view on MFA,
  (b) applying `hasManagerApproval` universally instead of only where
  specified, (c) allowing operators to rotate.
