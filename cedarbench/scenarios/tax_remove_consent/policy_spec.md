# Tax Preparer Permissions -- Policy Specification (No Consent)

## Context

This policy governs access control for a tax preparation platform within the
`Taxpreparer` namespace. The system has Professionals, Documents, and Clients.

Professionals have `assigned_orgs: Set<orgInfo>` where each orgInfo contains
`organization`, `serviceline`, and `location` strings.

Documents have `serviceline`, `location`, and `owner: Client` attributes.
Clients have an `organization: String`.

A context record with `consent: Consent` is still present in the schema but
there is NO consent enforcement rule.

## Requirements

### 1. Organization-Level Access
- A Professional may **viewDocument** if the professional's `assigned_orgs`
  set contains a record matching the document's owner organization, serviceline,
  and location:
  `principal.assigned_orgs.contains({organization: resource.owner.organization, serviceline: resource.serviceline, location: resource.location})`.

### 2. Ad-Hoc Access (Per Linked Template)
- Individual (principal, resource) pairs may be granted ad-hoc viewDocument
  access via linked policy templates:
  `permit(principal == ?principal, action == Taxpreparer::Action::"viewDocument", resource == ?resource)`.

## Notes
- There is NO forbid rule for consent. Access is granted purely based on
  organization matching or ad-hoc template linkage.
- The Consent type remains in the schema but is not enforced by any policy.
- All entities and actions are in the `Taxpreparer` namespace.
