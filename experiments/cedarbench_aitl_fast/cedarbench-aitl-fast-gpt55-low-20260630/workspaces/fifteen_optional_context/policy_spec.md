---
pattern: federated identity with many optional attestations
difficulty: hard
features:
  - 15 optional context attributes
  - has-guard discipline (§8.3 stress)
  - conjunction of 5 has-guarded reads
domain: identity / federation
synthesis_difficulty: 4
---

# Federated Resource Access — Many Optional Attestations

## Problem

A federated identity gateway sits in front of a sensitive resource. At
request time, upstream identity providers may have produced any subset
of fifteen independent attestations about the request — MFA, device,
location, identity-proofing, compliance flags, risk score, etc. Each
attestation is delivered as an OPTIONAL boolean in the request context.

For policy verifiability the gateway requires a fixed conjunction of
five SPECIFIC attestations to be present and `true`:

  1. `mfaToken` — MFA token presented and valid
  2. `deviceTrusted` — device posture check passed
  3. `locationVerified` — geolocation matches expected region
  4. `identityProofed` — identity proofing record on file
  5. `auditLoggingEnabled` — request will be audit-logged

The other ten attestations (`complianceFlag`, `riskAssessmentDone`,
`nonRepudiationSigned`, `biometricVerified`, `networkSegmentTrusted`,
`encryptionAttested`, `sessionFresh`, `rateLimitOk`, `geographicAllowed`,
`contractValid`) are accepted by the schema for forward compatibility
but not required for this action.

## Schema

- `entity User`
- `entity Resource`
- `action accessFederatedResource` over `(User, Resource)` with a context
  containing fifteen optional booleans.

## Rule

`accessFederatedResource` is permitted iff ALL FIVE of the required
attestations are PRESENT in context AND each evaluates to `true`. Each
optional read MUST be `has`-guarded before being read (§8.3); a missing
attestation must NOT crash the policy or be treated as `true`.

## Why this is hard

Cedar's type-checker rejects any read of an optional attribute that is
not provably guarded. A 5-clause conjunction with five paired
`has` checks and five reads stresses the `has`-guard discipline harder
than typical real-world policies — exactly the regime where the
synthesizer is most prone to drop a guard.
