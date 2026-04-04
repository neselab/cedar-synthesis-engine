# Clinical Trial Data Platform -- Policy Specification (Full Expansion)

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator, GlobalAuditor, DataManager).
Documents belong to Projects and have a `studyPhase` attribute. Project
attributes (status, managingDepartment) are denormalized onto Document
for policy evaluation.

## Requirements

### 1. Active Project Gate
- A user may only **View** or **Edit** a document if the document's
  `projectStatus == "Active"`. Documents in non-active projects are
  inaccessible.

### 2. Role Gate
- Only users in the **ClinicalResearcher**, **PrincipalInvestigator**,
  or **DataManager** role may View or Edit documents. All other users
  are denied by default.

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
- **Exception**: GlobalAuditors are exempt via an `unless` clause.

### 6. Auditor Loophole
- The **GlobalAuditor** role is exempt from the cross-departmental block.

### 7. DataManager Role
- A **DataManager** (checked via `principal in Role::"DataManager"`)
  may View and Edit documents (including `"HighlyRestricted"` classification)
  only if `principal.clearanceLevel > 5`.
- DataManagers are subject to the active project gate and the
  cross-departmental block with auditor loophole.

### 8. Study Phase Restriction
- Documents with `studyPhase == "Phase-3"` may ONLY be accessed by
  **PrincipalInvestigator** or **DataManager** roles.
- ClinicalResearchers are blocked from Phase-3 documents even if they
  otherwise satisfy all other constraints.

### 9. Patient Consent Requirement (Forbid)
- **Forbid** the **Edit** action if `context.hasPatientConsent == false`.
- View is NOT affected by consent status.
- This forbid has NO exceptions -- it applies to all roles.

### 10. Device Compliance Block for Highly Restricted Documents (Forbid)
- **Forbid** any View or Edit of documents with
  `resource.classification == "HighlyRestricted"` if
  `context.isCompliantDevice != true`.
- This forbid has NO exceptions. Even GlobalAuditors must use a
  compliant device to access HighlyRestricted documents.

## Notes
- This is the most complex variant with THREE forbid rules:
  1. Cross-departmental block (unless GlobalAuditor)
  2. Consent block on Edit (no exceptions)
  3. Device compliance block on HighlyRestricted (no exceptions)
- Three roles provide access via different paths: ClinicalResearcher
  (clearance + classification), PrincipalInvestigator (network + device),
  DataManager (high clearance, can access HighlyRestricted).
- Phase-3 restriction further limits ClinicalResearcher access.
