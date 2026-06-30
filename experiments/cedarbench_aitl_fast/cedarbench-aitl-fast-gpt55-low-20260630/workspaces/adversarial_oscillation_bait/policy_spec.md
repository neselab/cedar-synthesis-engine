---
pattern: adversarial oscillation bait — fix-A-break-B by construction
difficulty: hard (planning)
features:
  - role-based access (admin / user / guest)
  - classification gating (public / internal / confidential)
  - contractor flag with inverted semantics
  - MFA gate as confidential precondition
  - owner-bypass with MFA-on-confidential carve-out (§8.8)
  - three parallel actions (read / write / delete)
domain: enterprise document store / data classification
synthesis_difficulty: 4
---

# Adversarial Oscillation Bait — Policy Specification

## Context

This policy governs access to classified enterprise resources by users
in three roles. It is designed to maximize the **fix-A-break-B
oscillation** potential of an iterative synthesizer: each requirement
in §3 is "close to" but in tension with another. A naive code change
that satisfies one floor almost always violates the safety ceiling in
a different cell.

This scenario is a deliberate stress test of:
- **§8.1 directional feedback** — without distinguishing "this fix
  made the floor pass but broke the ceiling in cell X," the
  synthesizer cannot localize the regression.
- **§8.2 hash-based oscillation detection** — the synthesizer is
  highly likely to revisit prior candidates if the feedback is not
  precisely localized.
- **§8.6 role-intersection trap** — encoding "block contractors from
  confidential" as a `forbid when principal.isContractor &&
  resource.classification == "confidential"` would block contractors
  who have MFA verified, breaking FLOOR_CONTRACTOR_MFA_CONFIDENTIAL.
- **§8.8 floor-bound consistency** — the owner-bypass floor MUST
  include the same MFA-on-confidential carve-out as the ceiling, or
  bounds become jointly unsatisfiable.

## Domain model

- **User** has `role` ("admin" / "user" / "guest"), `department`,
  and `isContractor` (Bool).
- **Resource** has `classification` ("public" / "internal" /
  "confidential"), an `owner` (User), and `requiresMfa` (Bool).
- **Actions:** `read`, `write`, `delete`. All three follow the same
  permission structure — the parallelism is intentional, so the
  synthesizer faces the same oscillation pattern across multiple
  actions.
- **Context:** `mfaVerified: Bool`.

## Requirements

The same five rules apply to all three actions (`read`, `write`,
`delete`). Below, "X" denotes any of these actions.

### 1. SAFETY CEILING — X is permitted ONLY when one of:
   1. `principal.role == "admin"`, OR
   2. **Owner bypass (MFA-gated on confidential):**
      `principal == resource.owner` AND
      (`resource.classification != "confidential"` OR
       `context.mfaVerified`), OR
   3. **Standard user, non-confidential, not contractor:**
      `principal.role == "user"` AND
      `principal.isContractor == false` AND
      `resource.classification != "confidential"`, OR
   4. **Contractor accessing confidential WITH MFA:**
      `principal.role == "user"` AND
      `principal.isContractor == true` AND
      `resource.classification == "confidential"` AND
      `context.mfaVerified == true`

   Anything outside these four disjuncts MUST be denied. In
   particular: guests are NEVER permitted; contractors on
   non-confidential resources via the user role are NEVER permitted
   (the only contractor permit path is clause 4); confidential access
   without MFA is NEVER permitted unless the principal is admin.

### 2. FLOOR_ADMIN — admins MUST be permitted to X
   - For every Resource and every context, if
     `principal.role == "admin"`, X MUST be permitted.

### 3. FLOOR_OWNER — resource owner MUST be permitted to X (with §8.8 carve-out)
   - If `principal == resource.owner`, X MUST be permitted UNLESS
     the resource is confidential AND `context.mfaVerified == false`
     AND `principal.role != "admin"`.
   - Equivalently: owner is permitted when
     (`role == "admin"` OR `classification != "confidential"`
      OR `context.mfaVerified`).
   - **§8.8 NOTE:** the carve-out is required for floor-bound
     consistency with the ceiling. Without it, an owner-contractor
     of a confidential resource without MFA would be a permit-floor
     point that lies outside the ceiling.

### 4. FLOOR_USER_INTERNAL — user (non-contractor) MUST X internal resources
   - If `principal.role == "user"` AND `principal.isContractor == false`
     AND `resource.classification == "internal"`, X MUST be permitted.

### 5. FLOOR_CONTRACTOR_MFA_CONFIDENTIAL — contractor + MFA MUST X confidential
   - If `principal.role == "user"` AND `principal.isContractor == true`
     AND `resource.classification == "confidential"` AND
     `context.mfaVerified == true`, X MUST be permitted.

## Why this oscillates (planner's note)

Each "naive fix" introduces a CEILING violation in a different cell:

- Adding `permit when principal.role == "admin"` satisfies FLOOR_ADMIN
  but does nothing for FLOOR_OWNER, FLOOR_USER_INTERNAL,
  FLOOR_CONTRACTOR_MFA_CONFIDENTIAL.
- Adding a generic `permit when principal == resource.owner`
  satisfies FLOOR_OWNER but breaks the CEILING — a non-admin
  owner-contractor of a confidential resource without MFA gets
  permitted, which clause 4 of the ceiling forbids.
- Adding `permit when principal.role == "user" &&
  resource.classification == "internal"` satisfies FLOOR_USER_INTERNAL
  but admits user-contractors on internal resources, which the
  ceiling forbids.
- Adding `permit when principal.isContractor &&
  resource.classification == "confidential" &&
  context.mfaVerified` satisfies FLOOR_CONTRACTOR_MFA_CONFIDENTIAL
  but might also admit contractors with `role != "user"` (e.g.,
  guest) — which clauses 1-4 of the ceiling forbid.
- Adding `forbid when principal.isContractor &&
  resource.classification == "confidential"` (the §8.6 trap) breaks
  FLOOR_CONTRACTOR_MFA_CONFIDENTIAL because the forbid fires even
  when MFA is verified.

The intended converged candidate combines four narrowly-scoped
permits (one per ceiling clause) with no global forbid. The
synthesizer must arrive there without falling into any of the traps
above, which is exactly the workload §8.1 / §8.2 / §8.6 / §8.8 are
designed to handle.

## Non-requirements

- Guests have no permits; the dataset includes no floor for them.
- The `requiresMfa` attribute is informational; the policy gates on
  `classification == "confidential"`, not on `requiresMfa`. The
  attribute exists in the schema to add realistic noise.
- The `department` attribute is informational and does not appear in
  any rule.
