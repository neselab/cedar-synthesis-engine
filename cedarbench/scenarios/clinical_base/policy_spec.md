# Policy Specification — Clinical Trial Data Platform

Write Cedar policies to control **View** and **Edit** actions on Documents in a clinical trial system.

## Entity Model

- **User** has `department` (String), `clearanceLevel` (Long). Users are members of Roles.
- **Role** — named roles: `ClinicalResearcher`, `PrincipalInvestigator`, `GlobalAuditor`.
- **Project** has `status` (String) and `managingDepartment` (String).
- **Document** has `classification` (String). Documents belong to Projects (hierarchy). `projectStatus` and `projectManagingDepartment` are denormalized from the parent Project for policy access.
- **Context** carries `networkRiskScore` (Long) and `isCompliantDevice` (Bool).

## Access Control Requirements

### 1. Active Project Gate
A User can only View or Edit a Document if that Document's project currently has status `"Active"` (`resource.projectStatus == "Active"`).

### 2. Role Gate
The User must be a member of either `Role::"ClinicalResearcher"` or `Role::"PrincipalInvestigator"`.

### 3. Clinical Researcher Conditions
If the user is a Clinical Researcher, they can access the document **only if**:
- Their `clearanceLevel` is **strictly greater than 3** (`principal.clearanceLevel > 3`)
- AND the Document's `classification` is **not** `"HighlyRestricted"`

### 4. Principal Investigator Conditions
If the user is a Principal Investigator, they bypass clearance and classification checks. However:
- The request context must show `networkRiskScore < 20`
- AND `isCompliantDevice == true`

### 5. Cross-Departmental Block (Strict Deny)
**Regardless of any permits above**, write an explicit `forbid` policy that denies access if the User's `department` does not match the Document's `projectManagingDepartment`.

### 6. Auditor Loophole
The **only** exception to rule 5: if the user is a member of `Role::"GlobalAuditor"`, the cross-departmental block does not apply. Auditors still cannot access non-Active projects (rule 1 still applies).

## Difficulty Analysis
- **Forbid/permit interaction**: Cedar forbid always wins, so the cross-departmental forbid overrides even valid permits. The `unless` clause must be used for the auditor exception.
- **Multi-role membership**: A User can be both a GlobalAuditor and a ClinicalResearcher.
- **Numeric comparisons**: Strictly greater than 3 (not ≥ 3) and strictly less than 20.
- **4-dimensional constraint space**: role × clearance × classification × project status × department match × context.
