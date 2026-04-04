# Clinical Trial Data Platform -- Policy Specification

## Context

This policy governs access control for a clinical trial data platform with
Users, Roles, Projects, and Documents. Users belong to Roles (e.g.,
ClinicalResearcher, PrincipalInvestigator). Documents belong to Projects.
Project attributes (status, managingDepartment) are denormalized onto
Document for policy evaluation.

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
- There are NO exceptions to this rule. Even GlobalAuditors are blocked
  by department mismatch.

## Notes
- Roles are checked via entity group membership: `principal in Role::"ClinicalResearcher"`.
- Cedar denies by default; no explicit deny-all policy is needed.
- The GlobalAuditor loophole has been removed. The forbid rule has no `unless` clause.
