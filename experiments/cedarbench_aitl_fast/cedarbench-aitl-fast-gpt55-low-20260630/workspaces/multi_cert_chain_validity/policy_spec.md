---
pattern: multi-cert chain validity (3-way interval intersection)
difficulty: medium
features:
  - datetime comparison
  - 3-way temporal interval intersection
  - 6-comparison conjunction
domain: PKI / certificate validation
synthesis_difficulty: 3
---

# Multi-Cert Chain Validity -- Policy Specification

## Context

This policy gates a "secure" action behind validation of an entire
certificate chain at the moment of the request. Three independent
certificates must ALL be simultaneously valid:

1. The end user's client certificate (`User.userCertValidFrom` /
   `User.userCertValidUntil`)
2. The user's organization's certificate (`Organization.orgCertValidFrom`
   / `Organization.orgCertValidUntil`)
3. The certificate authority that signed the chain
   (`CertAuthority.caCertValidFrom` / `CertAuthority.caCertValidUntil`)

A certificate is "valid at time T" iff `validFrom <= T <= validUntil`.
The request is permitted iff all three intervals contain `context.now`.

Entities:
- `User` with `userCertValidFrom: datetime`, `userCertValidUntil: datetime`
- `Organization` with `orgCertValidFrom: datetime`,
  `orgCertValidUntil: datetime`
- `Resource` with `requiredCa: CertAuthority` (the CA whose chain
  must validate for this resource)
- `CertAuthority` with `caCertValidFrom: datetime`,
  `caCertValidUntil: datetime`

Context: `now: datetime`, `userOrg: Organization` (the org the user
is acting on behalf of -- the host application populates this from
the user's session).

Action: `accessSecure`.

## Requirements

### 1. Secure Access Requires All Three Cert Chains Valid (Permit)

A `User` may perform the `accessSecure` action on a `Resource` if and
ONLY if ALL of the following six datetime comparisons hold at request
time:

- User cert lower bound: `context.now >= principal.userCertValidFrom`
- User cert upper bound: `context.now <= principal.userCertValidUntil`
- Org cert lower bound:  `context.now >= context.userOrg.orgCertValidFrom`
- Org cert upper bound:  `context.now <= context.userOrg.orgCertValidUntil`
- CA cert lower bound:   `context.now >= resource.requiredCa.caCertValidFrom`
- CA cert upper bound:   `context.now <= resource.requiredCa.caCertValidUntil`

If any single one of these comparisons fails, the request must be
denied. There is no override, no admin bypass, and no role-based
exception. The chain either validates at the precise moment of the
request or the request is denied.

## Notes

- All six comparisons are simple `datetime` comparisons. The host
  application is responsible for populating `context.now` from a
  trusted clock source and `context.userOrg` from the user's session.
- The naive encoding is a six-clause `&&` conjunction. The common
  failure modes hunted by this scenario are:
  - Reversing the direction of a comparison (writing `<=` where `>=`
    is required, or vice versa).
  - Confusing `validFrom` (a lower bound on `now`) with `validUntil`
    (an upper bound on `now`).
  - Forgetting one of the three certs entirely.
- Cedar denies by default, so the absence of a permit when any cert
  is invalid is sufficient to deny.
- All three cert validity windows are independent. They may overlap
  partially or fully or not at all. The policy only cares about the
  3-way intersection containing `context.now`.
