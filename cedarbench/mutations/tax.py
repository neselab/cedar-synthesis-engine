"""Tax preparer permissions mutations."""

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

# -- Base policy spec (shared starting point) ---------------------------------

_BASE_SPEC = """\
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
"""


# -- Helpers -------------------------------------------------------------------

def _tax_base_schema() -> str:
    """The base tax_preparer schema."""
    return """\
namespace Taxpreparer {
  type orgInfo = {
    organization: String,
    serviceline: String,
    location: String,
  };
  // A tax-preparing professional
  entity Professional = {
    assigned_orgs: Set<orgInfo>,
    location: String,
  };
  // A client's tax document
  entity Document = {
    serviceline: String,
    location: String,
    owner: Client,
  };
  // A client
  entity Client = {
    organization: String
  };
  // The record of consent from a client to view a doc
  type Consent = {
    client: Client,
    team_region_list: Set<String>
  };

  action viewDocument appliesTo {
    principal: [Professional],
    resource: [Document],
    context: { consent: Consent }
  };
}
"""


# -- Easy Mutations ------------------------------------------------------------

class TaxRemoveConsent(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_remove_consent",
            base_scenario="tax",
            difficulty="easy",
            description="Remove consent forbid rule; org-matching and ad-hoc only",
            operators=["P3"],
            features_tested=["simplification", "forbid_removal"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        # Schema is unchanged -- the consent type stays but the forbid rule is removed from spec
        schema = _tax_base_schema()
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class TaxAddEdit(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_add_edit",
            base_scenario="tax",
            difficulty="easy",
            description="Add editDocument action with same constraints as viewDocument",
            operators=["S7", "P2"],
            features_tested=["new_action", "constraint_replication"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
namespace Taxpreparer {
  type orgInfo = {
    organization: String,
    serviceline: String,
    location: String,
  };
  entity Professional = {
    assigned_orgs: Set<orgInfo>,
    location: String,
  };
  entity Document = {
    serviceline: String,
    location: String,
    owner: Client,
  };
  entity Client = {
    organization: String
  };
  type Consent = {
    client: Client,
    team_region_list: Set<String>
  };

  action viewDocument appliesTo {
    principal: [Professional],
    resource: [Document],
    context: { consent: Consent }
  };

  action editDocument appliesTo {
    principal: [Professional],
    resource: [Document],
    context: { consent: Consent }
  };
}
"""
        spec = _BASE_SPEC + """\
### 4. Edit Document Permissions
- A new **editDocument** action is available on Documents.
- **editDocument** follows the SAME access rules as viewDocument:
  - Organization-level access: the professional's `assigned_orgs` must contain
    a matching record for the document's owner organization, serviceline, and location.
  - Ad-hoc access: individual (principal, resource) pairs can be granted.
- The consent requirement also applies to editDocument:
  - `context.consent.client == resource.owner` AND
  - `context.consent.team_region_list.contains(principal.location)`.
- Both the organization-matching permit and the consent forbid/unless must
  reference both `viewDocument` and `editDocument`.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Medium Mutations ----------------------------------------------------------

class TaxAddSupervisor(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_add_supervisor",
            base_scenario="tax",
            difficulty="medium",
            description="Add Supervisor entity that bypasses serviceline and location matching",
            operators=["S6", "P2", "P4"],
            features_tested=["new_entity", "privilege_escalation", "partial_bypass"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
namespace Taxpreparer {
  type orgInfo = {
    organization: String,
    serviceline: String,
    location: String,
  };
  entity Professional = {
    assigned_orgs: Set<orgInfo>,
    location: String,
  };
  entity Supervisor = {
    supervised_orgs: Set<String>,
    location: String,
  };
  entity Document = {
    serviceline: String,
    location: String,
    owner: Client,
  };
  entity Client = {
    organization: String
  };
  type Consent = {
    client: Client,
    team_region_list: Set<String>
  };

  action viewDocument appliesTo {
    principal: [Professional, Supervisor],
    resource: [Document],
    context: { consent: Consent }
  };
}
"""
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class TaxAddSensitivity(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_add_sensitivity",
            base_scenario="tax",
            difficulty="medium",
            description="Add isSensitive Bool on Document; sensitive docs require HQ in team_region_list",
            operators=["S1", "P1", "P10"],
            features_tested=["boolean_guard", "context_constraint", "additional_forbid"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
namespace Taxpreparer {
  type orgInfo = {
    organization: String,
    serviceline: String,
    location: String,
  };
  entity Professional = {
    assigned_orgs: Set<orgInfo>,
    location: String,
  };
  entity Document = {
    serviceline: String,
    location: String,
    owner: Client,
    isSensitive: Bool,
  };
  entity Client = {
    organization: String
  };
  type Consent = {
    client: Client,
    team_region_list: Set<String>
  };

  action viewDocument appliesTo {
    principal: [Professional],
    resource: [Document],
    context: { consent: Consent }
  };
}
"""
        spec = _BASE_SPEC + """\
### 4. Sensitive Document Restriction (Deny Rule)
- Document now has an `isSensitive: Bool` attribute.
- If a document has `isSensitive == true`, the **viewDocument** action is
  **forbidden** unless the consent's `team_region_list` contains the
  string `"HQ"`.
- Specifically: `forbid ... when { resource.isSensitive } unless { context.consent.team_region_list.contains("HQ") }`.
- This is an ADDITIONAL restriction on top of the existing consent requirement.
  For sensitive documents, the professional's location must be in the consent
  region list (existing rule) AND the region list must include "HQ" (new rule).
- Non-sensitive documents are unaffected by this rule.

## Notes (Sensitivity)
- The sensitive-document forbid interacts with the existing consent forbid.
  Both forbids must be satisfied (i.e., neither must block) for access to proceed.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class TaxAddClientProfile(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_add_client_profile",
            base_scenario="tax",
            difficulty="medium",
            description="Add viewClientProfile action on Client; org-matching only, no consent needed",
            operators=["S7", "P2", "P7"],
            features_tested=["new_action", "different_resource_type", "no_context"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
namespace Taxpreparer {
  type orgInfo = {
    organization: String,
    serviceline: String,
    location: String,
  };
  entity Professional = {
    assigned_orgs: Set<orgInfo>,
    location: String,
  };
  entity Document = {
    serviceline: String,
    location: String,
    owner: Client,
  };
  entity Client = {
    organization: String
  };
  type Consent = {
    client: Client,
    team_region_list: Set<String>
  };

  action viewDocument appliesTo {
    principal: [Professional],
    resource: [Document],
    context: { consent: Consent }
  };

  action viewClientProfile appliesTo {
    principal: [Professional],
    resource: [Client],
  };
}
"""
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Hard Mutations ------------------------------------------------------------

class TaxAddAuditor(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_add_auditor",
            base_scenario="tax",
            difficulty="hard",
            description="Add Auditor entity that bypasses org matching but still needs consent",
            operators=["S6", "P2", "P4", "P5"],
            features_tested=["new_entity", "partial_bypass", "consent_still_applies"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
namespace Taxpreparer {
  type orgInfo = {
    organization: String,
    serviceline: String,
    location: String,
  };
  entity Professional = {
    assigned_orgs: Set<orgInfo>,
    location: String,
  };
  entity Auditor = {
    location: String,
    auditScope: Set<String>,
  };
  entity Document = {
    serviceline: String,
    location: String,
    owner: Client,
  };
  entity Client = {
    organization: String
  };
  type Consent = {
    client: Client,
    team_region_list: Set<String>
  };

  action viewDocument appliesTo {
    principal: [Professional, Auditor],
    resource: [Document],
    context: { consent: Consent }
  };
}
"""
        spec = _BASE_SPEC + """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


class TaxFullExpansion(Mutation):
    def meta(self):
        return MutationMeta(
            id="tax_full_expansion",
            base_scenario="tax",
            difficulty="hard",
            description="Supervisor + sensitivity + editDocument + auditor all combined",
            operators=["S6", "S6", "S7", "S1", "P1", "P2", "P2", "P4", "P5", "P10"],
            features_tested=["multi_mutation", "multi_entity", "multi_action", "complex_forbids"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
namespace Taxpreparer {
  type orgInfo = {
    organization: String,
    serviceline: String,
    location: String,
  };
  entity Professional = {
    assigned_orgs: Set<orgInfo>,
    location: String,
  };
  entity Supervisor = {
    supervised_orgs: Set<String>,
    location: String,
  };
  entity Auditor = {
    location: String,
    auditScope: Set<String>,
  };
  entity Document = {
    serviceline: String,
    location: String,
    owner: Client,
    isSensitive: Bool,
  };
  entity Client = {
    organization: String
  };
  type Consent = {
    client: Client,
    team_region_list: Set<String>
  };

  action viewDocument appliesTo {
    principal: [Professional, Supervisor, Auditor],
    resource: [Document],
    context: { consent: Consent }
  };

  action editDocument appliesTo {
    principal: [Professional, Supervisor],
    resource: [Document],
    context: { consent: Consent }
  };
}
"""
        spec = """\
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
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Registration --------------------------------------------------------------

MUTATIONS = [
    TaxRemoveConsent(),
    TaxAddEdit(),
    TaxAddSupervisor(),
    TaxAddSensitivity(),
    TaxAddClientProfile(),
    TaxAddAuditor(),
    TaxFullExpansion(),
]

for m in MUTATIONS:
    register(m)
