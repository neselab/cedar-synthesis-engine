# Sales Organization — Policy Specification

## Context

This policy governs access control for a contracted sales organization
("ABC"). The system has two protected resources, `Presentation` and
`Template`, and a single principal type, `User`. Users are differentiated
by a `job` enumeration attribute (internal, distributor, customer, or
other), and may belong to zero or more `Market` groups.

The creator of a resource is its `owner` and may carry out any action on
that resource. Other users gain access by being added to a per-resource
ACL as one of two roles: **viewer** or **editor**. Templates additionally
allow access via Market membership — the template can list viewer Markets
and editor Markets, granting access to all Users within those markets.

The permissions a viewer/editor receives depend on the User's `job`. Some
actions are restricted to internal users only, others are available to all
permitted users.

## Entity Model

- **Job** is an enumeration entity used as a typed tag on Users. Logical
  values are `"internal"`, `"distributor"`, `"customer"`, and `"other"`.
- **User** is the principal type. Users are members of zero or more
  Markets (`User in [Market]`). Each User has:
  - `job: Job` — the job type
  - `customerId: String` — distributor and customer association key;
    irrelevant when `job` is internal.
- **Market** is a group entity used to group Users for Template access.
- **Presentation** is a protected resource with `owner: User`,
  `viewers: Set<User>`, and `editors: Set<User>`.
- **Template** is a protected resource with `owner: User`,
  `viewers: Set<User>`, `editors: Set<User>`, plus Market-based access:
  `viewerMarkets: Set<Market>` and `editorMarkets: Set<Market>`.

## Action Groups

The schema groups actions semantically:

- **InternalPrezViewActions**: viewing actions on Presentations that any
  internal-job user with view rights can perform.
- **ExternalPrezViewActions**: viewing actions on Presentations that
  external (non-internal) viewers can also perform.
- **PrezEditActions**: editing/management actions on Presentations,
  available only to editors.
- **InternalTemplateViewActions**: viewing actions on Templates available
  to internal-job users with view rights.
- **MarketTemplateViewActions**: viewing actions on Templates available
  via Market membership (which can be either internal or external users).
- **TemplateEditActions**: editing/management actions on Templates,
  available only to editors.

The concrete actions are slotted into these groups by the schema (see
`schema.cedarschema`):
- `viewPresentation`, `removeSelfAccessFromPresentation` are in
  Internal+External Prez view groups and in PrezEdit (the owner/editor
  can always view; viewers can also remove their own access).
- `duplicatePresentation` is in Internal Prez view (only internal users
  can duplicate, since it creates a new resource).
- `editPresentation`, `grantViewAccessToPresentation`,
  `grantEditAccessToPresentation` are in PrezEdit only.
- `viewTemplate`, `duplicateTemplate` are in Internal Template view, in
  Market Template view, AND in Template edit (any of those grants the
  right to view/duplicate).
- `removeSelfAccessFromTemplate` is in Internal Template view and in
  Template edit (it's the right to drop your own ACL slot).
- `editTemplate`, `removeOthersAccessToTemplate`,
  `grantViewAccessToTemplate`, `grantEditAccessToTemplate` are in
  Template edit only.

## Requirements

### 1. Owner Always Has Full Access
- The `owner` of a Presentation may perform any action in
  `PrezEditActions` (which transitively includes the view groups) on
  that Presentation.
- The `owner` of a Template may perform any action in
  `TemplateEditActions` on that Template.

### 2. Presentation View Access (Internal Job)
- A User whose `job == Job::"internal"` may perform any action in
  `InternalPrezViewActions` on a Presentation if `principal in
  resource.viewers`.

### 3. Presentation View Access (External Job)
- A User whose `job != Job::"internal"` may perform any action in
  `ExternalPrezViewActions` on a Presentation if `principal in
  resource.viewers`. External viewers do NOT get duplicate access
  (because `duplicatePresentation` is in InternalPrez only).

### 4. Presentation Edit Access (Internal-Only)
- A User listed in `resource.editors` of a Presentation may perform any
  action in `PrezEditActions` ONLY IF the user's `job == Job::"internal"`.
  External users may not be granted editor access (this is enforced both
  by the rule above and by the grant restrictions in §6).

### 5. Template View Access
- A User listed in `resource.viewers` of a Template may perform any
  action in `InternalTemplateViewActions` if their `job == Job::"internal"`,
  and any action in `MarketTemplateViewActions` regardless of job.
- A User who is a member of a Market in `resource.viewerMarkets` may
  perform any action in `MarketTemplateViewActions` on the Template,
  regardless of their job.

### 6. Template Edit Access (Internal-Only)
- A User listed in `resource.editors` of a Template may perform any
  action in `TemplateEditActions` ONLY IF their `job == Job::"internal"`.
- A User who is a member of a Market in `resource.editorMarkets` may
  perform any action in `TemplateEditActions` ONLY IF their `job ==
  Job::"internal"`. Market-based editor access is internal-only.

### 7. Grant Access Rules — Distributor → Customer Only
- The `grantViewAccessToPresentation` and `grantEditAccessToPresentation`
  actions take a `target: User` in their `context`. When the target user
  has `job == Job::"customer"`, the granting principal must have
  `job == Job::"distributor"` AND `principal.customerId ==
  context.target.customerId`. In other words, only the distributor that a
  customer is assigned to may share resources with that customer.
- For non-customer targets, the standard editor restriction applies (the
  granting principal must be the owner or an editor; targets that would
  receive *editor* access must themselves be internal — see §8).

### 8. Editor Grants Are Internal-Only
- `grantEditAccessToPresentation` and `grantEditAccessToTemplate`
  (whether via direct user ACL or Market) require the target user to be
  internal: only internal users may be granted editor access. Customers,
  distributors, and other external users may receive viewer access but
  never editor access.

### 9. Template Grants — Market or User Target
- The `grantViewAccessToTemplate` and `grantEditAccessToTemplate` actions
  take an optional `targetMarket?: Market` and an optional `targetUser?:
  User` in their context — exactly one of which is set per request.
  Grants targeting a Market follow the editor-internal rule above for
  edit grants; grants targeting a User follow the same rules as
  Presentation grants in §7 and §8.

## Notes
- Cedar denies by default; only the listed permits grant access.
- Optional context attributes (`targetMarket?`, `targetUser?`) on the
  template-grant actions must be guarded with `has` before they are read,
  per Cedar's type-checker requirements.
- The customer/distributor matching uses string comparison on
  `customerId`, not entity identity.
- The distinction between `InternalPrezViewActions` and
  `ExternalPrezViewActions` exists so that some Presentation view actions
  (specifically `duplicatePresentation`) can be restricted to internal
  users while others (`viewPresentation`, `removeSelfAccessFromPresentation`)
  remain available to both internal and external viewers.
