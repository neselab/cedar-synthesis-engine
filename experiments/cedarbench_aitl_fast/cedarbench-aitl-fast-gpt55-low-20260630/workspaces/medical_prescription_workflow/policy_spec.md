---
pattern: medical prescription workflow
difficulty: hard
features:
  - role-based access (physician, pharmacist, patient, nurse)
  - resource ownership (prescriber, patient)
  - boolean state guard (isFilled)
  - optional context attribute with has-guard (controlledSubstanceVerified)
  - conditional context requirement (controlled substances only)
domain: healthcare
synthesis_difficulty: 3
---

# Medical Prescription Workflow -- Policy Specification

## Context

This policy governs a controlled-substance prescription workflow in a
healthcare system. Four roles interact with prescriptions: physicians
create them, pharmacists review and fill them, patients view their own,
and nurses view any prescription for care coordination.

The key safety property: filling a controlled-substance prescription
requires an additional verification attestation (`controlledSubstanceVerified`)
carried in request context by the dispensing system.

## Entity Model

- **User**: the principal. Has a `role` attribute (one of `"physician"`,
  `"pharmacist"`, `"patient"`, `"nurse"`).
- **Prescription**: the resource. Has:
  - `prescriber: User` -- the physician who created the prescription.
  - `patient: User` -- the patient the prescription is for.
  - `isControlled: Bool` -- whether this is a controlled substance.
  - `isFilled: Bool` -- whether the prescription has already been dispensed.

## Request Context

- `controlledSubstanceVerified?: Bool` -- optional attribute. Present and
  `true` when the dispensing system has verified DEA schedule compliance
  for a controlled substance. Must be `has`-guarded before any read
  (Cedar negated-has trap, section 8.3).

## Actions

- `create` -- write a new prescription into the system.
- `review` -- read/examine a prescription's details.
- `fill` -- dispense the prescribed medication.
- `viewHistory` -- view the prescription history for a patient.

## Requirements

### 1. Create (Physician Only)

Only users with `role == "physician"` may create prescriptions. No other
role may create, regardless of other attributes.

### 2. Review (Role- and Ownership-Gated)

Three categories of users may review a prescription:
- **Pharmacist**: any pharmacist may review any prescription
  (`role == "pharmacist"`).
- **Physician**: may review only prescriptions they wrote
  (`role == "physician"` AND `principal == resource.prescriber`).
- **Patient**: may review only their own prescriptions
  (`role == "patient"` AND `principal == resource.patient`).

Nurses may NOT review prescriptions (they use viewHistory instead).

### 3. Fill (Pharmacist, State + Controlled-Substance Gate)

Only pharmacists may fill a prescription, subject to two guards:
- The prescription must not already be filled (`!resource.isFilled`).
- If the prescription is a controlled substance (`resource.isControlled`),
  the context must attest verification:
  `context has controlledSubstanceVerified && context.controlledSubstanceVerified == true`.

For non-controlled substances, the `controlledSubstanceVerified` context
attribute need not be present.

Expressed as a single condition: `!resource.isFilled` AND
(`!resource.isControlled` OR (`context has controlledSubstanceVerified`
AND `context.controlledSubstanceVerified == true`)).

### 4. View History (Ownership + Nurse Care Coordination)

Three categories of users may view prescription history:
- **Patient**: may view history of their own prescriptions
  (`role == "patient"` AND `principal == resource.patient`).
- **Physician**: may view history of prescriptions they wrote
  (`role == "physician"` AND `principal == resource.prescriber`).
- **Nurse**: may view history of any prescription for care coordination
  (`role == "nurse"`).

Pharmacists may NOT view history (they use review instead).

## Notes

- The `controlledSubstanceVerified` attribute is optional. The fill
  ceiling must use the `has`-guard pattern:
  `(!(context has controlledSubstanceVerified) || (context has controlledSubstanceVerified && ...))` is NOT sufficient
  for the ceiling -- the ceiling must express: if isControlled, then
  the context MUST have and satisfy controlledSubstanceVerified.
- Cedar denies by default; no explicit forbid policies are needed.
- The fill action's dual guard (isFilled + controlled-substance check)
  is the central safety property.
- Floors must be jointly satisfiable with ceilings per section 8.8.
