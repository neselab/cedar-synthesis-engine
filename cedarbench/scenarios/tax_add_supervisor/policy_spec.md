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
### 4. Supervisor Access
- A new **Supervisor** entity type exists with `supervised_orgs: Set<String>`
  (a set of organization names) and `location: String`.
- Supervisors may **viewDocument** if the document's owner organization is in
  the supervisor's `supervised_orgs` set:
  `principal.supervised_orgs.contains(resource.owner.organization)`.
- Unlike Professionals, Supervisors do NOT need to match the document's
  `serviceline` or `location`. Organization-level matching is sufficient.
- The consent requirement STILL applies to Supervisors:
  `context.consent.client == resource.owner` AND
  `context.consent.team_region_list.contains(principal.location)`.
- The viewDocument action now accepts both `[Professional, Supervisor]` as principals.

## Notes (Supervisor)
- The Supervisor permit is a separate, more relaxed rule than the Professional permit.
- Both Professional and Supervisor are subject to the same consent forbid/unless.
