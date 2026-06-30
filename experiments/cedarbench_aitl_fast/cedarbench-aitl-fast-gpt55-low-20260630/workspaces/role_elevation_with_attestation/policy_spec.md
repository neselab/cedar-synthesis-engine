---
pattern: role elevation with attestation
difficulty: hard
features:
  - optional context attribute
  - non-empty string attestation
  - role + grant + justification conjunction
  - has-guard for optional context
domain: security / privileged access
synthesis_difficulty: 3
---

# Role Elevation With Attestation — Policy Specification

## Context

This policy implements a **temporary role elevation with justification
attestation** pattern. Some users have a base role (`"user"`, `"lead"`,
or `"manager"`) which controls everyday access, but may also be granted
**temporary elevation** to access sensitive resources. Elevation is
gated on two checks:

1. The user must have `elevationGranted == true` on their User entity
   (set by an out-of-band privileged-access workflow), AND
2. The current request must include a **non-empty justification string**
   in the `elevationJustification` context attribute. This is a
   compliance/audit requirement: every elevated access must have a
   recorded business reason.

Managers do not require elevation to access sensitive resources — they
have standing authority. Users and leads must use the
elevation-with-justification pattern.

## Entities

- **User** — `baseRole: String` (one of `"user"`, `"lead"`, `"manager"`)
  and `elevationGranted: Bool` (whether the elevation grant is active).
- **SensitiveResource** — no attributes; the entity tag itself indicates
  sensitivity classification.

## Context attributes

| Attribute                  | Type             | Notes                              |
|----------------------------|------------------|------------------------------------|
| `elevationJustification`   | String, OPTIONAL | Free-text business justification.  |

The `elevationJustification` context attribute is **optional** in the
schema (declared with `?`). Any read MUST be `has`-guarded.

## Actions

- **accessNormal** — applies to `User` × `SensitiveResource`. Routine
  access requests.
- **accessSensitive** — applies to `User` × `SensitiveResource`.
  Privileged access requiring either standing manager authority or
  attestation-backed elevation.

## Access rules

### 1. accessNormal

Permitted when `principal.baseRole` is one of `"user"`, `"lead"`, or
`"manager"`. (All three roles may perform normal access. There is no
elevation requirement for normal access.)

### 2. accessSensitive

Permitted in either of two disjoint cases:

- **Case A (manager standing authority):**
  `principal.baseRole == "manager"`. No further conditions.

- **Case B (elevation with attestation):**
  `principal.baseRole == "user"` OR `principal.baseRole == "lead"`,
  AND `principal.elevationGranted == true`,
  AND `context has elevationJustification`,
  AND `context.elevationJustification != ""`.

A non-empty justification string is mandatory under Case B; an empty
string `""` does NOT count as a valid attestation.

## Notes

- The non-empty string check can be encoded as
  `context.elevationJustification != ""` (string equality) or as
  `context.elevationJustification like "?*"` (anchored: at least one
  character). Both are valid Cedar idioms.
- The `has`-guard pattern is required because `elevationJustification`
  is an optional context attribute. Reading it without first checking
  `context has elevationJustification` will fail Cedar validation.
- Common failure modes:
  (a) forgetting the `has`-guard before reading
  `context.elevationJustification`,
  (b) accepting elevation without a justification (allowing
  `elevationGranted == true` alone to grant access),
  (c) accepting an empty justification string as valid,
  (d) requiring elevation/justification of managers (managers have
  standing authority and should not need either).
