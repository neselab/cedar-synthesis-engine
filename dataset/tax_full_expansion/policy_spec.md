# Tax Preparer Permissions -- Policy Specification (Full Expansion)

## Context

This policy governs access control for a tax preparation platform within the
`Taxpreparer` namespace. The system has Professionals, Supervisors, Auditors,
Documents, and Clients.

Professionals have `assigned_orgs: Set<orgInfo>` and `location: String`.
Supervisors have `supervised_orgs: Set<String>` and `location: String`.
Auditors have `location: String` and `auditScope: Set<String>`.
Documents have `serviceline`, `location`, `owner: Client`, and `isSensitive: Bool`.
Clients have `organization: String`.

Context contains `consent: Consent` with `client: Client` and `team_region_list: Set<String>`.

## Requirements

### 1. Professional Organization-Level Access (viewDocument & editDocument)
- A Professional may **viewDocument** or **editDocument** if
  `principal.assigned_orgs.contains({organization: resource.owner.organization, serviceline: resource.serviceline, location: resource.location})`.

### 2. Supervisor Access (viewDocument & editDocument)
- A Supervisor may **viewDocument** or **editDocument** if
  `principal.supervised_orgs.contains(resource.owner.organization)`.
- Supervisors bypass serviceline and location matching on the document.

### 3. Auditor Access (viewDocument only)
- An Auditor may **viewDocument** if
  `principal.auditScope.contains(resource.serviceline)`.
- Auditors bypass organization matching entirely. They may view documents
  from any organization as long as the serviceline is in scope.
- Auditors may NOT editDocument -- they have view-only access.

### 4. Ad-Hoc Access (viewDocument only)
- Individual (principal, resource) pairs may be granted ad-hoc viewDocument
  access via linked policy templates.

### 5. Consent Requirement (Deny Rule -- applies to ALL actions)
- All **viewDocument** and **editDocument** access is **forbidden** unless:
  - `context.consent.client == resource.owner`, AND
  - `context.consent.team_region_list.contains(principal.location)`.
- This applies to Professionals, Supervisors, and Auditors alike.

### 6. Sensitive Document Restriction (Deny Rule)
- If `resource.isSensitive == true`, **viewDocument** and **editDocument** are
  **forbidden** unless `context.consent.team_region_list.contains("HQ")`.
- This applies to all principal types (Professional, Supervisor, Auditor).

## Notes
- Three principal types with different access patterns:
  Professional (full org match), Supervisor (org-only match), Auditor (serviceline-only match).
- Two actions: viewDocument (all three principals) and editDocument (Professional + Supervisor only).
- Two forbid rules: consent (universal) and sensitivity (conditional on isSensitive).
- Both forbids apply to both actions and all applicable principal types.
