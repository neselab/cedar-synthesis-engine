# Emergency Break-Glass — Policy Specification

## Context

This policy governs access to patient medical Records at a hospital. The
primary principal is `Clinician`; the primary resource is `Record`. Every
Clinician, Patient, and Record is associated with a Hospital entity (we
enforce same-hospital as a baseline).

Two actions are defined: `viewRecord` and `editRecord`. Both take a
context object with `emergencyActive: Bool` and `emergencyReason: String`.

The policy implements a strict care-team access model **plus** a narrowly
scoped emergency break-glass override for viewing.

## Requirements

### 1. Same-Hospital Baseline (Forbid)
- **Forbid** any action on a Record when the Clinician's `hospital` does
  not match the Record's `hospital`. Cross-hospital access is never
  permitted, and no override applies to this rule.

### 2. Care-Team Standard Access (Permit)
- A Clinician may **viewRecord** or **editRecord** on a Record when the
  Record's patient is in the Clinician's `careTeamPatients` set:
  `resource.patient in principal.careTeamPatients`.
- No additional conditions apply to care-team access — no emergency, no
  attestation.

### 3. Break-Glass View-Only Access (Permit)
- A Clinician who is **NOT** on the Record's patient's care team may
  still **viewRecord** if ALL of the following hold:
  - The clinician is currently in the hospital's on-call pool:
    `principal.isOnCall == true`, AND
  - The request's context declares an active emergency:
    `context.emergencyActive == true`, AND
  - The clinician has attested a non-empty reason:
    `context.emergencyReason != ""`.
- Break-glass applies to the `viewRecord` action only. **Editing is
  never authorized by break-glass, regardless of emergency state or
  on-call status.** Edit access is always restricted to care-team
  clinicians.

### 4. Same-Hospital Constraint on Break-Glass
- Break-glass access still requires the same-hospital baseline from §1.
  A clinician cannot break-glass into another hospital's records under
  any circumstance, even if they are on-call and have declared an
  emergency. The §1 forbid overrides the break-glass permit.

## Notes
- Cedar denies by default. The per-permit rules in §2 and §3 grant
  access; the forbid in §1 overrides both.
- Break-glass is a *narrow* override: three conditions must all hold
  (on-call, emergency active, reason attested), and it unlocks only one
  action (viewRecord). The common error in policies like this is to
  drop one condition (e.g. forget to check `emergencyReason`) or to
  accidentally authorize editing via break-glass.
- The `emergencyReason` attestation check uses string non-emptiness
  (`!= ""`). Cedar does not provide string-length operators, but string
  equality works, so `context.emergencyReason != ""` is the idiomatic
  check for "reason was supplied".
- Both on-call and non-on-call clinicians retain full care-team access
  regardless of emergency state. Break-glass is strictly additive.
