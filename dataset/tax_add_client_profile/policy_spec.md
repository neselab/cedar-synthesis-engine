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
### 4. View Client Profile Permissions
- A new **viewClientProfile** action is available, targeting **Client** resources
  (not Documents).
- A Professional may **viewClientProfile** if any entry in the professional's
  `assigned_orgs` has an `organization` matching the client's `organization`.
  Specifically, there must exist an orgInfo in `principal.assigned_orgs` where
  `orgInfo.organization == resource.organization`.
- Note: Since `assigned_orgs` is a `Set<orgInfo>` and Cedar does not have
  existential quantification over sets of records, the practical approach is
  to check if `principal.assigned_orgs` contains a record with the matching
  organization. However, serviceline and location in the orgInfo do not need
  to match any specific value on the Client -- only the organization matters.
- The consent requirement does NOT apply to viewClientProfile -- this action
  has no context requirement. The consent forbid only applies to viewDocument.

## Notes (Client Profile)
- viewClientProfile targets Client entities, not Documents.
- The consent forbid is scoped to `action == Taxpreparer::Action::"viewDocument"`,
  so it does not affect viewClientProfile.
