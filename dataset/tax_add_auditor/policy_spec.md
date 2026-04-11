# Tax Preparer Permissions -- Policy Specification

## Context

This policy governs access control for a tax preparation platform within the
`Taxpreparer` namespace. The system has Professionals, Documents, and Clients.

Professionals have `assigned_orgs: Set<orgInfo>` where each orgInfo contains
`organization`, `serviceline`, and `location` strings. They also have a
`location: String` attribute.

Documents have `serviceline`, `location`, and `owner: Client` attributes.
Clients have an `organization: String`.

Access requires a context record containing `consent: Consent`, where Consent
has `client: Client` and `team_region_list: Set<String>`.

## Requirements

### 1. Organization-Level Access
- A Professional may **viewDocument** if the professional's `assigned_orgs`
  set contains a record matching the document's owner organization, serviceline,
  and location. Specifically:
  `principal.assigned_orgs.contains({organization: resource.owner.organization, serviceline: resource.serviceline, location: resource.location})`.

### 2. Ad-Hoc Access (Per Linked Template)
- Individual (principal, resource) pairs may be granted ad-hoc viewDocument
  access via linked policy templates. These are expressed as:
  `permit(principal == ?principal, action == Taxpreparer::Action::"viewDocument", resource == ?resource)`.

### 3. Consent Requirement (Deny Rule)
- All viewDocument access is **forbidden** unless the consent context satisfies:
  - `context.consent.client == resource.owner` (consent is from the document's owner), AND
  - `context.consent.team_region_list.contains(principal.location)` (the professional's
    location is in the consent's team region list).
- This forbid/unless applies universally -- it blocks both organization-level
  and ad-hoc access unless consent is provided.

## Notes
- All entities and actions are in the `Taxpreparer` namespace.
- The consent forbid uses an `unless` clause to express the requirement.
- Cedar denies by default; the consent forbid is an additional restriction
  on top of the permit rules.
### 4. Auditor Access
- A new **Auditor** entity type exists with `location: String` and
  `auditScope: Set<String>` (a set of serviceline names the auditor may review).
- An Auditor may **viewDocument** if the document's `serviceline` is in
  the auditor's `auditScope`:
  `principal.auditScope.contains(resource.serviceline)`.
- Unlike Professionals, Auditors do NOT need organization-level matching.
  They can view documents from any organization, as long as the serviceline
  is in their audit scope.
- The consent requirement STILL applies to Auditors:
  `context.consent.client == resource.owner` AND
  `context.consent.team_region_list.contains(principal.location)`.
- The viewDocument action now accepts both `[Professional, Auditor]` as principals.

## Notes (Auditor)
- The Auditor permit is: `permit (principal is Taxpreparer::Auditor, action == Taxpreparer::Action::"viewDocument", resource) when { principal.auditScope.contains(resource.serviceline) }`.
- The consent forbid/unless applies universally to all viewDocument access,
  regardless of principal type. Both Professional and Auditor are subject to it.
- Auditors bypass org matching but not consent. This tests partial privilege escalation.
