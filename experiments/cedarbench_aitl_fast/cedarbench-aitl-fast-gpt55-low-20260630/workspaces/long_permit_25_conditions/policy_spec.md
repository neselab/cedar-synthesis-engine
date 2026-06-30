---
pattern: long permit with 25 AND-chained conditions
difficulty: hard
features:
  - 25-clause AND conjunction
  - mixed boolean / numeric / string / datetime predicates
  - context + principal + resource attribute interplay
  - deny-by-default with single permit gate
domain: enterprise security / audit-heavy access
synthesis_difficulty: 3
---

# Long Permit (25 AND Conditions) — Policy Specification

## Context

This scenario stress-tests the model's ability to assemble a single
permit policy whose `when` clause is a long conjunction (25+ AND-ed
conditions) covering identity, device, environment, resource, and
compliance facts. Production access controls in regulated industries
(finance, defense, healthcare) frequently look like this: a single
"all of the following must hold" gate that touches dozens of
attributes from the principal, resource, and context.

There is **one action** (`accessSensitive`) and **one permit policy**.
A request is permitted only if every one of the 25 conditions holds.
There are no global forbids and no other permits.

## Entities

- **User** — attributes:
  - `role: String` — must be `"employee"` (contractors get a separate floor).
  - `mfaVerified: Bool`
  - `clearanceLevel: Long`
  - `dept: String`
  - `isContractor: Bool`
  - `complianceTrainingCurrent: Bool`
  - `nda: Bool`
  - `nonDisclosureSigned: Bool`
  - `backgroundCheckPassed: Bool`
- **Resource** — attributes:
  - `classification: String` — one of `"public"`, `"internal"`, `"confidential"`, `"restricted"`.
  - `ownerDept: String`
  - `requiresClearance: Long`
  - `archived: Bool`
  - `requiresNda: Bool`
  - `complianceFlag: Bool`

## Context attributes

| Attribute          | Type     | Meaning                                    |
|--------------------|----------|--------------------------------------------|
| `now`              | datetime | current time                                |
| `mfaTimestamp`     | datetime | time of last MFA challenge                  |
| `currentLocation`  | String   | one of `"office"`, `"home"`, `"travel"`     |
| `vpnConnected`     | Bool     | corporate VPN connection active             |
| `riskScore`        | Long     | risk engine score, 0–100 (lower = safer)    |
| `incidentMode`     | Bool     | true if SOC has declared an active incident |

## Action

`accessSensitive` — the only action. Applies to `User` × `Resource`.

## Access rule (single permit, 25 AND conditions)

A request is permitted **iff every one of the following holds**:

1. `principal.role == "employee"`
2. `principal.mfaVerified`
3. `context.now.durationSince(context.mfaTimestamp) < duration("1h")` (MFA recent)
4. `principal.clearanceLevel >= resource.requiresClearance`
5. `principal.dept == resource.ownerDept`
6. `!resource.archived`
7. `!principal.isContractor`
8. `principal.complianceTrainingCurrent`
9. `principal.backgroundCheckPassed`
10. `context.vpnConnected`
11. `context.riskScore <= 50`
12. `!context.incidentMode`
13. `context.currentLocation != "travel"`
14. `resource.classification != "public"` (this gate is for sensitive material only)
15. `resource.classification != "restricted"` (restricted requires a separate top-secret flow not modeled here)
16. `principal.clearanceLevel >= 2`
17. `principal.clearanceLevel <= 5` (sanity bound)
18. `resource.requiresClearance >= 1`
19. `(!resource.requiresNda) || principal.nda`
20. `(!resource.requiresNda) || principal.nonDisclosureSigned`
21. `(!resource.complianceFlag) || principal.complianceTrainingCurrent`
22. `context.riskScore >= 0`
23. `principal.dept != ""`
24. `resource.ownerDept != ""`
25. `principal.mfaVerified && context.vpnConnected` (paranoid duplicate of 2 ∧ 10)

The clause is intentionally redundant in places (16/17/18 are sanity
bounds; 21 doubles 8 conditional on the resource flag; 25 duplicates
2∧10). Real production policies often grow this way as auditors layer
in checks; the harness must still synthesize a single permit covering
all of them.

## Notes

- Deny-by-default: with no other permits, anything that fails any
  one of the 25 conditions is denied automatically.
- Liveness exists: an employee in the right department, with MFA fresh
  on the corporate VPN, low risk, no incident, in the office, with
  clearance level ≥ resource requirement, accessing a non-archived
  internal/confidential document with NDA + compliance satisfied,
  IS permitted.
- Common failure modes:
  - Dropping a condition (most likely the redundant ones 16–25).
  - Confusing `requiresNda` polarity — `requiresNda=false` should
    NOT block a user without NDA.
  - Using ISO-8601 duration syntax instead of Go-style (§8.9).
