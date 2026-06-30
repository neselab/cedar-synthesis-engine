---
pattern: purpose-of-use / minimum-necessary / compliance-attestation
difficulty: hard
features:
  - role-purpose-category matrix (3-way conjunction)
  - optional context attribute with has-guard (patientAuthorized)
  - action-specific context requirements (disclosureLog for disclose)
  - authorization override (patient consent bypasses minimum necessary)
domain: healthcare / compliance / HIPAA
synthesis_difficulty: 4
---

# HIPAA Minimum Necessary — Policy Specification

## Context

This policy implements the HIPAA Privacy Rule's **Minimum Necessary
Standard** (§164.502(b)) for workforce access to Protected Health
Information (PHI). When a workforce member requests PHI for a use or
disclosure, the covered entity must make reasonable efforts to limit the
PHI to the minimum necessary to accomplish the purpose.

Our encoding enforces this as a role-purpose-category matrix: a workforce
member's role determines which `declaredPurpose` values are legitimate,
and the purpose in turn restricts which `dataCategory` of PatientRecord
they may touch. The request must carry a purpose attestation
(`context.purposeAttested == true`) — this is the purpose-of-use marker
required by the Privacy Rule.

Two statutory carve-outs apply:
1. **Treatment exception (§164.502(b)(2)(i))** — disclosures to a
   provider for treatment of an individual are explicitly exempt from
   the minimum-necessary restriction. We encode this by letting a
   clinician with `declaredPurpose == "treatment"` access *any*
   `dataCategory`.
2. **Patient authorization (§164.508)** — a patient-executed
   authorization overrides minimum necessary. We encode this as an
   optional `context.patientAuthorized` attribute: when present and
   true, the role-purpose-category matrix is waived (but attestation
   and audit logging are still required).

Principal is `Workforce`; resource is `PatientRecord`. Three actions:
`view`, `disclose`, `amend`.

## Role-Purpose-Category Matrix

| Role              | Declared Purpose | Allowed dataCategory           |
|-------------------|------------------|--------------------------------|
| clinician         | treatment        | any (treatment exception)      |
| billing           | payment          | "billing" or "demographic"     |
| researcher        | research         | "research" only                |
| privacy_officer   | operations       | any (oversight)                |

Any other role-purpose pairing is forbidden. Any other
role-purpose-category triple is forbidden (subject to the patient-
authorization override).

## Requirements

### 1. Attestation Gate (all actions)
Every request must have `context.purposeAttested == true`. A request
without attestation MUST be denied regardless of role or purpose.

### 2. View Access
A Workforce member may `view` a PatientRecord when:
- `context.purposeAttested == true`, AND
- **EITHER** the role-purpose-category matrix is satisfied:
  - `role == "clinician"` AND `context.declaredPurpose == "treatment"`
    (any `dataCategory` allowed — treatment exception), OR
  - `role == "billing"` AND `context.declaredPurpose == "payment"` AND
    `resource.dataCategory in {"billing", "demographic"}`, OR
  - `role == "researcher"` AND `context.declaredPurpose == "research"`
    AND `resource.dataCategory == "research"`, OR
  - `role == "privacy_officer"` AND
    `context.declaredPurpose == "operations"` (any `dataCategory` — for
    compliance oversight).
- **OR** `context has patientAuthorized && context.patientAuthorized == true`
  (patient-authorized disclosure — role-purpose-category waived but
  attestation still required).

### 3. Disclose Access
Same as `view` **PLUS** `context.disclosureLog == true` (the
disclosure must be attested to the audit log per §164.528 accounting-
of-disclosures requirements).

### 4. Amend Access
Tighter than view/disclose. Only a clinician, declaring treatment
purpose, may amend — and only on the clinical category:
- `role == "clinician"` AND
- `context.declaredPurpose == "treatment"` AND
- `context.purposeAttested == true` AND
- `resource.dataCategory == "clinical"`.
- The patient-authorization override does NOT apply to `amend`
  (amendment rights flow through §164.526 and are not a §164.508
  authorization).

### 5. Cedar encoding hazards

- **Optional-attribute has-guard (§8.3).** The `patientAuthorized`
  field is optional. Any read MUST be preceded by a `has` check
  combined under `&&`, not under a negated disjunction. The canonical
  guarded form is:
  `context has patientAuthorized && context.patientAuthorized`.
  When the override branch is optional (i.e., "accept if unset OR set
  to true"), the safe idiom is
  `!(context has patientAuthorized) || (context has patientAuthorized && context.patientAuthorized)`.
  Cedar's type-checker does NOT propagate negation through `has`, so
  never write `!(context has X) || context.X`.
- **Floor-bound consistency (§8.8).** Every floor must be jointly
  satisfiable with every ceiling. For example, a floor asserting
  "clinician must be permitted to view clinical" must include
  `context.declaredPurpose == "treatment"` and
  `context.purposeAttested == true` in its guard — otherwise the
  ceiling for view will exclude cases where attestation is false, and
  the floor will be unsatisfiable against it.
- **String-enum matrix.** Cedar has no enums. The role-purpose-
  category matrix is expressed as a disjunction of four conjunctive
  branches, one per role. Avoid collapsing branches — each branch has
  distinct category scoping.

## Notes on HIPAA grounding

- §164.502(b) establishes the minimum-necessary rule for use and
  disclosure of PHI.
- §164.502(b)(2)(i) explicitly exempts disclosures to health-care
  providers for treatment purposes.
- §164.508 governs written authorizations from individuals; an
  executed authorization can waive the minimum-necessary ceiling for
  the disclosures it covers.
- §164.526 (amendment of PHI) is deliberately NOT encoded as a
  workforce-permission here — the policy only gates the clinician's
  ability to invoke an amendment workflow.
- §164.528 (accounting of disclosures) motivates the
  `disclosureLog` attestation on `disclose`.
