# Clinical Trial Data Platform -- Policy Specification

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator, GlobalAuditor). Documents
belong to Projects. Project attributes (status, managingDepartment)
are denormalized onto Document for policy evaluation.

## Requirements

### 1. Active Project Gate
- A user may only **View** or **Edit** a document if the document's
  `projectStatus == "Active"`. Documents in non-active projects are
  inaccessible.

### 2. Role Gate
- Only users in the **ClinicalResearcher** or **PrincipalInvestigator**
  role may View or Edit documents. All other users are denied by default.

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

### 6. Device Compliance Block for Highly Restricted Documents (Forbid)
- **Forbid** any View or Edit of documents with
  `resource.classification == "HighlyRestricted"` if
  `context.isCompliantDevice != true` (i.e., the device is non-compliant).
- This forbid has NO exceptions. Even GlobalAuditors must use a
  compliant device to access HighlyRestricted documents.

## Notes
- There are TWO independent forbid rules in this scenario.
- The GlobalAuditor is exempt from the cross-departmental block (requirement 5)
  but is NOT exempt from the device compliance block (requirement 6).
- This tests correct handling of multiple forbid rules with different exemption scopes.
- Cedar denies by default; no explicit deny-all policy is needed.
