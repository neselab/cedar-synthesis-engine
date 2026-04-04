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

### 6. Auditor Loophole
- The **GlobalAuditor** role is exempt from the cross-departmental block
  (via an `unless` clause on the forbid rule). GlobalAuditors may access
  documents outside their department, provided they otherwise qualify
  under the permit rules.

## Notes
- Roles are checked via entity group membership: `principal in Role::"ClinicalResearcher"`.
- Cedar denies by default; no explicit deny-all policy is needed.
- The forbid/unless pattern is the key complexity driver in this scenario.
### 7. Temporal Embargo (Forbid with Exception)
- Documents now have an `embargoUntil` attribute (Long, representing a
  Unix epoch timestamp).
- A new context field `requestTime` (Long, Unix epoch timestamp) is added
  to both View and Edit actions.
- **Forbid** any View or Edit if `context.requestTime < resource.embargoUntil`
  (i.e., the request is made before the embargo lifts).
- **Exception**: PrincipalInvestigators (`principal in Role::"PrincipalInvestigator"`)
  are exempt from this embargo via an `unless` clause. PIs can access
  embargoed documents early.
- This forbid is independent of the cross-departmental block. Both may
  apply simultaneously.

## Notes (Temporal Embargo)
- The embargo uses Long (integer) timestamps rather than a dedicated datetime
  type for Cedar compatibility.
- The embargo forbid uses a numeric less-than comparison on context vs resource.
- Two forbid rules now exist, each with different `unless` exceptions:
  cross-dept block (unless GlobalAuditor) and embargo (unless PI).
