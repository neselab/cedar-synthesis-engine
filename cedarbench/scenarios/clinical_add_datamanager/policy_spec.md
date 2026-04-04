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
- This forbid overrides all permit rules.

### 6. Auditor Loophole
- The **GlobalAuditor** role is exempt from the cross-departmental block
  (via an `unless` clause on the forbid rule). GlobalAuditors may access
  documents outside their department, provided they otherwise qualify
  under the permit rules.

## Notes
- Roles are checked via entity group membership: `principal in Role::"ClinicalResearcher"`.
- Cedar denies by default; no explicit deny-all policy is needed.
- The forbid/unless pattern is the key complexity driver in this scenario.
### 7. DataManager Constraints
- A **DataManager** is a new role (checked via `principal in Role::"DataManager"`).
- A DataManager may **Edit** documents (including `"HighlyRestricted"` classification)
  only if `principal.clearanceLevel > 5`.
- A DataManager may also **View** documents under the same clearance constraint.
- DataManagers are still subject to the active project gate (requirement 1)
  and the cross-departmental block with auditor loophole (requirements 5 and 6).
- Unlike ClinicalResearchers, DataManagers CAN access HighlyRestricted documents
  (provided their clearanceLevel > 5).
