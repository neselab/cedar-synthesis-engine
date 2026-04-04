# Clinical Trial Data Platform -- Policy Specification

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator, GlobalAuditor,
SponsorRepresentative). Documents belong to Projects. Project attributes
(status, managingDepartment) are denormalized onto Document for policy
evaluation. Documents also have a `studyPhase` attribute.

## Requirements

### 1. Active Project Gate
- A user may only **View** or **Edit** a document if the document's
  `projectStatus == "Active"`. Documents in non-active projects are
  inaccessible.

### 2. Role Gate
- Only users in the **ClinicalResearcher**, **PrincipalInvestigator**,
  or **SponsorRepresentative** role may access documents. All other
  users are denied by default.

### 3. Clinical Researcher Constraints
- A ClinicalResearcher may View/Edit a document only if:
  - `principal.clearanceLevel > 3`, AND
  - `resource.classification != "HighlyRestricted"`.

### 4. Principal Investigator Constraints
- A PrincipalInvestigator may View/Edit a document only if:
  - `context.networkRiskScore < 20`, AND
  - `context.isCompliantDevice == true`.

### 5. Cross-Departmental Block (Forbid)
- **Forbid** any View or Edit if the user's `department` does not match
  the document's `projectManagingDepartment`.
- This forbid overrides all permit rules.
- **Exception**: GlobalAuditors (`principal in Role::"GlobalAuditor"`) are
  exempt from this block via an `unless` clause.
- **Exception**: SponsorRepresentatives are also exempt from this block,
  but ONLY for the **View** action (see requirement 7).

### 6. Auditor Loophole
- The **GlobalAuditor** role is exempt from the cross-departmental block
  for both View and Edit actions.

### 7. SponsorRepresentative Constraints
- A **SponsorRepresentative** is a new role
  (checked via `principal in Role::"SponsorRepresentative"`).
- A SponsorRepresentative may **View** documents only. They may NOT **Edit**.
- SponsorRepresentatives are exempt from the cross-departmental block
  for View only. They can view documents from any department.
- SponsorRepresentatives may ONLY view documents where
  `resource.studyPhase == "Phase-3"`. Phase-1 and Phase-2 documents
  are not accessible to them.
- SponsorRepresentatives are still subject to the active project gate.

## Notes
- Three roles now provide View access via different paths: ClinicalResearcher
  (clearance + classification), PrincipalInvestigator (network + device),
  and SponsorRepresentative (Phase-3 only, View only, cross-dept exempt).
- The cross-departmental forbid now has TWO exception paths: GlobalAuditor
  (all actions) and SponsorRepresentative (View only).
- Cedar denies by default; no explicit deny-all policy is needed.
