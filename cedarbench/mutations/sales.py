"""Sales organization permissions mutations."""

from cedarbench.mutation import Mutation, MutationMeta, MutationResult, register
from cedarbench import schema_ops

# -- Base policy spec (shared starting point) ---------------------------------

_BASE_SPEC = """\
# Sales Organization Permissions -- Policy Specification

## Context

This policy governs access control for a sales organization platform with
Users, Markets, Presentations, Templates, and Jobs.

Users belong to Markets (via `User in [Market]`) and have a `job: Job` attribute
(with entity values like `Job::"internal"`, `Job::"distributor"`, `Job::"customer"`)
and a `customerId: String`.

Presentations have `owner: User`, `viewers: Set<User>`, and `editors: Set<User>`.
Templates have `owner: User`, `viewers: Set<User>`, `editors: Set<User>`,
`viewerMarkets: Set<Market>`, and `editorMarkets: Set<Market>`.

Actions are organized into action groups:
- Presentation actions: InternalPrezViewActions, ExternalPrezViewActions, PrezEditActions
- Template actions: InternalTemplateViewActions, MarketTemplateViewActions, TemplateEditActions

## Requirements

### 1. External Presentation View
- A user may perform **ExternalPrezViewActions** (viewPresentation,
  removeSelfAccessFromPresentation) if `principal in resource.viewers`.

### 2. Internal Presentation View
- A user may perform **InternalPrezViewActions** (viewPresentation,
  removeSelfAccessFromPresentation, duplicatePresentation) if
  `principal.job == Job::"internal"` AND `principal in resource.viewers`.

### 3. Presentation Edit
- A user may perform **PrezEditActions** (viewPresentation,
  removeSelfAccessFromPresentation, duplicatePresentation, editPresentation,
  grantViewAccessToPresentation, grantEditAccessToPresentation) if
  `resource.owner == principal` OR `principal in resource.editors`.

### 4. Customer Sharing Restriction (Deny Rule)
- When granting view access to a presentation, the action
  **grantViewAccessToPresentation** is **forbidden** unless:
  - `context.target.job != Job::"customer"`, OR
  - (`principal.job == Job::"distributor"` AND
     `principal.customerId == context.target.customerId`).
- In other words: you cannot share view access with a customer user UNLESS
  you are a distributor sharing with your own customer (same customerId).

### 5. Internal-Only Edit Sharing (Deny Rule)
- **grantEditAccessToPresentation** is **forbidden** when
  `context.target.job != Job::"internal"`.
- Only internal users can receive edit access to presentations.

### 6. Market Template View
- A user may perform **MarketTemplateViewActions** (viewTemplate,
  duplicateTemplate) if `principal in resource.viewerMarkets`.

### 7. Internal Template View
- A user may perform **InternalTemplateViewActions** (viewTemplate,
  duplicateTemplate, removeSelfAccessFromTemplate) if
  `principal.job == Job::"internal"` AND `principal in resource.viewers`.

### 8. Template Edit
- A user may perform **TemplateEditActions** (viewTemplate, duplicateTemplate,
  removeSelfAccessFromTemplate, editTemplate, removeOthersAccessToTemplate,
  grantViewAccessToTemplate, grantEditAccessToTemplate) if
  `resource.owner == principal` OR `principal in resource.editors` OR
  `principal in resource.editorMarkets`.

### 9. Template View Grant Restriction (Deny Rule)
- **grantViewAccessToTemplate** is **forbidden** when the context specifies
  a `targetUser` AND that user is a customer AND the granting user is not
  a distributor sharing with their own customer:
  `context has targetUser && context.targetUser.job == Job::"customer" && (principal.job != Job::"distributor" || principal.customerId != context.targetUser.customerId)`.
- Market-targeted grants (`context has targetMarket`) are always allowed.

### 10. Template Edit Grant Restriction (Deny Rule)
- **grantEditAccessToTemplate** is **forbidden** when
  `context has targetUser && context.targetUser.job != Job::"internal"`.
- Market-targeted grants are always allowed.

## Notes
- Job types are entity references: `Job::"internal"`, `Job::"distributor"`,
  `Job::"customer"`, `Job::"other"`.
- The grant actions use context to specify the target of the grant.
- Market membership is checked via `principal in resource.viewerMarkets`
  because User is `in [Market]`.
- Cedar denies by default; the forbid rules are additional restrictions.
"""


# -- Helpers -------------------------------------------------------------------

def _sales_base_schema() -> str:
    """The base sales_orgs schema."""
    return """\
// Sales Organization Permissions -- Cedar Schema

// Entities
entity Job;
entity User in [Market] {
  job: Job,
  customerId: String,
};
entity Market;
entity Presentation {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
};
entity Template {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  viewerMarkets: Set<Market>,
  editorMarkets: Set<Market>,
};
// Actions -- Presentations
action InternalPrezViewActions;
action ExternalPrezViewActions;
action PrezEditActions;
action viewPresentation, removeSelfAccessFromPresentation
    in [InternalPrezViewActions, ExternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action duplicatePresentation in [InternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action editPresentation in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action grantViewAccessToPresentation, grantEditAccessToPresentation
    in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { target: User, },
  };

// Actions -- Templates
action InternalTemplateViewActions;
action MarketTemplateViewActions;
action TemplateEditActions;
action viewTemplate, duplicateTemplate
   in [InternalTemplateViewActions, TemplateEditActions,
       MarketTemplateViewActions]
  appliesTo {
    principal: User,
    resource: Template,
  };
action removeSelfAccessFromTemplate
   in [InternalTemplateViewActions, TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action editTemplate, removeOthersAccessToTemplate in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action grantViewAccessToTemplate, grantEditAccessToTemplate
    in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template,
    context: { targetMarket?: Market, targetUser?: User },
  };
"""


# -- Easy Mutations ------------------------------------------------------------

class SalesRemoveCustomerRestriction(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_remove_customer_restriction",
            base_scenario="sales",
            difficulty="easy",
            description="Remove forbid on customer sharing; anyone can grant view access to anyone",
            operators=["P3"],
            features_tested=["forbid_removal", "simplification"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _sales_base_schema()
        spec = """\
# Sales Organization Permissions -- Policy Specification (No Customer Restriction)

## Context

This policy governs access control for a sales organization platform with
Users, Markets, Presentations, Templates, and Jobs.

Users belong to Markets and have a `job: Job` and `customerId: String`.
Presentations and Templates have owner, viewers, editors, and (for Templates)
market-based access sets.

## Requirements

### 1. External Presentation View
- A user may perform **ExternalPrezViewActions** (viewPresentation,
  removeSelfAccessFromPresentation) if `principal in resource.viewers`.

### 2. Internal Presentation View
- A user may perform **InternalPrezViewActions** (viewPresentation,
  removeSelfAccessFromPresentation, duplicatePresentation) if
  `principal.job == Job::"internal"` AND `principal in resource.viewers`.

### 3. Presentation Edit
- A user may perform **PrezEditActions** if `resource.owner == principal` OR
  `principal in resource.editors`.

### 4. Internal-Only Edit Sharing (Deny Rule)
- **grantEditAccessToPresentation** is **forbidden** when
  `context.target.job != Job::"internal"`.

### 5. Market Template View
- A user may perform **MarketTemplateViewActions** if `principal in resource.viewerMarkets`.

### 6. Internal Template View
- A user may perform **InternalTemplateViewActions** if
  `principal.job == Job::"internal"` AND `principal in resource.viewers`.

### 7. Template Edit
- A user may perform **TemplateEditActions** if `resource.owner == principal`
  OR `principal in resource.editors` OR `principal in resource.editorMarkets`.

### 8. Template Edit Grant Restriction (Deny Rule)
- **grantEditAccessToTemplate** is **forbidden** when
  `context has targetUser && context.targetUser.job != Job::"internal"`.

## Notes
- The customer sharing restrictions for grantViewAccessToPresentation and
  grantViewAccessToTemplate have been REMOVED. Any user with edit permissions
  may grant view access to any other user, including customers.
- The internal-only edit sharing restrictions remain in place.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class SalesAddArchive(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_add_archive",
            base_scenario="sales",
            difficulty="easy",
            description="Add isArchived Bool on Presentation; forbid edit actions on archived presentations",
            operators=["S1", "P1"],
            features_tested=["boolean_guard", "forbid_rule"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Sales Organization Permissions -- Cedar Schema (with Archive)

entity Job;
entity User in [Market] {
  job: Job,
  customerId: String,
};
entity Market;
entity Presentation {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  isArchived: Bool,
};
entity Template {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  viewerMarkets: Set<Market>,
  editorMarkets: Set<Market>,
};
// Actions -- Presentations
action InternalPrezViewActions;
action ExternalPrezViewActions;
action PrezEditActions;
action viewPresentation, removeSelfAccessFromPresentation
    in [InternalPrezViewActions, ExternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action duplicatePresentation in [InternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action editPresentation in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action grantViewAccessToPresentation, grantEditAccessToPresentation
    in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { target: User, },
  };

// Actions -- Templates
action InternalTemplateViewActions;
action MarketTemplateViewActions;
action TemplateEditActions;
action viewTemplate, duplicateTemplate
   in [InternalTemplateViewActions, TemplateEditActions,
       MarketTemplateViewActions]
  appliesTo {
    principal: User,
    resource: Template,
  };
action removeSelfAccessFromTemplate
   in [InternalTemplateViewActions, TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action editTemplate, removeOthersAccessToTemplate in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action grantViewAccessToTemplate, grantEditAccessToTemplate
    in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template,
    context: { targetMarket?: Market, targetUser?: User },
  };
"""
        spec = _BASE_SPEC + """\
### 11. Archived Presentation Block (Deny Rule)
- Presentation now has an `isArchived: Bool` attribute.
- If a presentation has `isArchived == true`, ALL **PrezEditActions** are
  **forbidden**. This includes: editPresentation, grantViewAccessToPresentation,
  grantEditAccessToPresentation, and the edit-group variants of viewPresentation,
  duplicatePresentation, removeSelfAccessFromPresentation.
- More precisely: `forbid (principal, action in Action::"PrezEditActions", resource) when { resource.isArchived }`.
- View actions (ExternalPrezViewActions, InternalPrezViewActions) are still
  allowed on archived presentations.
- Templates are unaffected by this rule.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class SalesAddDelete(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_add_delete",
            base_scenario="sales",
            difficulty="easy",
            description="Add deletePresentation action; owner-only",
            operators=["S7", "P2"],
            features_tested=["new_action", "owner_only"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = _sales_base_schema() + """
// Delete action -- owner only
action deletePresentation appliesTo {
    principal: User,
    resource: Presentation,
  };
"""
        spec = _BASE_SPEC + """\
### 11. Delete Presentation
- A new **deletePresentation** action is available on Presentations.
- ONLY the **owner** of a presentation may delete it:
  `permit (principal, action == Action::"deletePresentation", resource) when { resource.owner == principal }`.
- Editors do NOT have delete permission, even though they have other edit actions.
- The customer sharing and internal-only edit restrictions do not apply to
  deletePresentation since it has no context/target.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Medium Mutations ----------------------------------------------------------

class SalesAddRegionalManager(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_add_regional_manager",
            base_scenario="sales",
            difficulty="medium",
            description="Add RegionalManager job type; can edit templates across markets they manage",
            operators=["S9", "P2", "P7"],
            features_tested=["new_job_type", "cross_market_access", "template_privilege"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Sales Organization Permissions -- Cedar Schema (with Regional Manager)

entity Job;
entity User in [Market] {
  job: Job,
  customerId: String,
  managedMarkets: Set<Market>,
};
entity Market;
entity Presentation {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
};
entity Template {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  viewerMarkets: Set<Market>,
  editorMarkets: Set<Market>,
};
// Actions -- Presentations
action InternalPrezViewActions;
action ExternalPrezViewActions;
action PrezEditActions;
action viewPresentation, removeSelfAccessFromPresentation
    in [InternalPrezViewActions, ExternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action duplicatePresentation in [InternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action editPresentation in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action grantViewAccessToPresentation, grantEditAccessToPresentation
    in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { target: User, },
  };

// Actions -- Templates
action InternalTemplateViewActions;
action MarketTemplateViewActions;
action TemplateEditActions;
action viewTemplate, duplicateTemplate
   in [InternalTemplateViewActions, TemplateEditActions,
       MarketTemplateViewActions]
  appliesTo {
    principal: User,
    resource: Template,
  };
action removeSelfAccessFromTemplate
   in [InternalTemplateViewActions, TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action editTemplate, removeOthersAccessToTemplate in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action grantViewAccessToTemplate, grantEditAccessToTemplate
    in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template,
    context: { targetMarket?: Market, targetUser?: User },
  };
"""
        spec = _BASE_SPEC + """\
### 11. Regional Manager Template Access
- User now has an optional `managedMarkets: Set<Market>` attribute.
- A user whose `job == Job::"regional_manager"` gains additional template
  edit permissions based on their managed markets.
- A regional manager may perform **TemplateEditActions** on a template if
  any of the template's `editorMarkets` overlap with the manager's
  `managedMarkets`. Specifically, the manager has edit access if the template's
  editorMarkets set contains a market that is also in the manager's managedMarkets.
- This is IN ADDITION to the normal template edit path (owner, editors, editorMarkets
  membership). The regional manager path provides an alternative way to get
  edit access to templates whose markets the manager oversees.
- All existing forbid rules (customer sharing, internal-only edit) still apply
  to regional managers.

## Notes (Regional Manager)
- The regional manager permit checks: `principal.job == Job::"regional_manager"`
  and uses market overlap between `principal.managedMarkets` and `resource.editorMarkets`.
- Regional manager is an internal job type, so it passes the internal-only
  edit sharing check when granting access.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class SalesAddApproval(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_add_approval",
            base_scenario="sales",
            difficulty="medium",
            description="Add isApproved Bool on Template; unapproved templates are view-only for non-internal",
            operators=["S1", "P1", "P5"],
            features_tested=["boolean_guard", "job_conditional_forbid", "template_restriction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Sales Organization Permissions -- Cedar Schema (with Template Approval)

entity Job;
entity User in [Market] {
  job: Job,
  customerId: String,
};
entity Market;
entity Presentation {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
};
entity Template {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  viewerMarkets: Set<Market>,
  editorMarkets: Set<Market>,
  isApproved: Bool,
};
// Actions -- Presentations
action InternalPrezViewActions;
action ExternalPrezViewActions;
action PrezEditActions;
action viewPresentation, removeSelfAccessFromPresentation
    in [InternalPrezViewActions, ExternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action duplicatePresentation in [InternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action editPresentation in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action grantViewAccessToPresentation, grantEditAccessToPresentation
    in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { target: User, },
  };

// Actions -- Templates
action InternalTemplateViewActions;
action MarketTemplateViewActions;
action TemplateEditActions;
action viewTemplate, duplicateTemplate
   in [InternalTemplateViewActions, TemplateEditActions,
       MarketTemplateViewActions]
  appliesTo {
    principal: User,
    resource: Template,
  };
action removeSelfAccessFromTemplate
   in [InternalTemplateViewActions, TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action editTemplate, removeOthersAccessToTemplate in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action grantViewAccessToTemplate, grantEditAccessToTemplate
    in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template,
    context: { targetMarket?: Market, targetUser?: User },
  };
"""
        spec = _BASE_SPEC + """\
### 11. Unapproved Template Restriction (Deny Rule)
- Template now has an `isApproved: Bool` attribute.
- If a template has `isApproved == false`, the following restrictions apply:
  - **Non-internal users** (users whose `job != Job::"internal"`) are
    restricted to view-only access. Specifically, **TemplateEditActions**
    and **MarketTemplateViewActions** that include duplicateTemplate are
    forbidden for non-internal users on unapproved templates.
  - More precisely: `forbid (principal, action in Action::"TemplateEditActions", resource) when { !resource.isApproved && principal.job != Job::"internal" }`.
  - **Internal users** can still perform all template actions on unapproved
    templates (they are not affected by this restriction).
- Presentation actions are unaffected by the template approval flag.

## Notes (Template Approval)
- The forbid checks two conditions: `!resource.isApproved` AND `principal.job != Job::"internal"`.
- Internal users bypass the approval gate entirely.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class SalesAddTeam(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_add_team",
            base_scenario="sales",
            difficulty="medium",
            description="Add Team entity for team-based presentation sharing",
            operators=["S6", "S9", "P2"],
            features_tested=["new_entity", "group_membership", "set_based_access"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Sales Organization Permissions -- Cedar Schema (with Teams)

entity Job;
entity Team;
entity User in [Market, Team] {
  job: Job,
  customerId: String,
};
entity Market;
entity Presentation {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  viewerTeams: Set<Team>,
  editorTeams: Set<Team>,
};
entity Template {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  viewerMarkets: Set<Market>,
  editorMarkets: Set<Market>,
};
// Actions -- Presentations
action InternalPrezViewActions;
action ExternalPrezViewActions;
action PrezEditActions;
action viewPresentation, removeSelfAccessFromPresentation
    in [InternalPrezViewActions, ExternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action duplicatePresentation in [InternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action editPresentation in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action grantViewAccessToPresentation, grantEditAccessToPresentation
    in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { target: User, },
  };

// Actions -- Templates
action InternalTemplateViewActions;
action MarketTemplateViewActions;
action TemplateEditActions;
action viewTemplate, duplicateTemplate
   in [InternalTemplateViewActions, TemplateEditActions,
       MarketTemplateViewActions]
  appliesTo {
    principal: User,
    resource: Template,
  };
action removeSelfAccessFromTemplate
   in [InternalTemplateViewActions, TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action editTemplate, removeOthersAccessToTemplate in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action grantViewAccessToTemplate, grantEditAccessToTemplate
    in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template,
    context: { targetMarket?: Market, targetUser?: User },
  };
"""
        spec = _BASE_SPEC + """\
### 11. Team-Based Presentation Access
- A new **Team** entity type exists. Users can belong to Teams
  (via `User in [Market, Team]`).
- Presentations now have `viewerTeams: Set<Team>` and `editorTeams: Set<Team>`
  attributes, similar to how Templates have market-based sets.
- A user may perform **ExternalPrezViewActions** (viewPresentation,
  removeSelfAccessFromPresentation) if `principal in resource.viewerTeams`
  (i.e., the user belongs to one of the presentation's viewer teams).
- A user may perform **PrezEditActions** if `principal in resource.editorTeams`
  (team-based edit access), in addition to the existing owner/editors paths.
- The team-based view path behaves like ExternalPrezViewActions -- it does NOT
  require `principal.job == Job::"internal"`.
- All existing forbid rules (customer sharing, internal-only edit) still apply
  to team-based access.

## Notes (Teams)
- Team membership is checked via `principal in resource.viewerTeams` because
  `User in [Market, Team]`.
- This mirrors the Market-based template access pattern but applied to presentations.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Hard Mutations ------------------------------------------------------------

class SalesTemporalCampaign(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_temporal_campaign",
            base_scenario="sales",
            difficulty="hard",
            description="Add campaignStart/End Long on Presentation; non-internal limited to time window",
            operators=["S2", "S2", "P1", "P4", "P10"],
            features_tested=["temporal_window", "numeric_comparison", "job_conditional_bypass"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Sales Organization Permissions -- Cedar Schema (with Temporal Campaigns)

entity Job;
entity User in [Market] {
  job: Job,
  customerId: String,
};
entity Market;
entity Presentation {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  campaignStart: Long,
  campaignEnd: Long,
};
entity Template {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  viewerMarkets: Set<Market>,
  editorMarkets: Set<Market>,
};
// Actions -- Presentations
action InternalPrezViewActions;
action ExternalPrezViewActions;
action PrezEditActions;
action viewPresentation, removeSelfAccessFromPresentation
    in [InternalPrezViewActions, ExternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { currentTime: Long },
  };
action duplicatePresentation in [InternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { currentTime: Long },
  };
action editPresentation in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { currentTime: Long },
  };
action grantViewAccessToPresentation, grantEditAccessToPresentation
    in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { target: User, currentTime: Long },
  };

// Actions -- Templates
action InternalTemplateViewActions;
action MarketTemplateViewActions;
action TemplateEditActions;
action viewTemplate, duplicateTemplate
   in [InternalTemplateViewActions, TemplateEditActions,
       MarketTemplateViewActions]
  appliesTo {
    principal: User,
    resource: Template,
  };
action removeSelfAccessFromTemplate
   in [InternalTemplateViewActions, TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action editTemplate, removeOthersAccessToTemplate in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action grantViewAccessToTemplate, grantEditAccessToTemplate
    in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template,
    context: { targetMarket?: Market, targetUser?: User },
  };
"""
        spec = _BASE_SPEC + """\
### 11. Campaign Time Window (Deny Rule with Internal Bypass)
- Presentation now has `campaignStart: Long` and `campaignEnd: Long` attributes,
  representing epoch timestamps for a campaign visibility window.
- All presentation actions now include `currentTime: Long` in their context.
- For **non-internal users** (users whose `job != Job::"internal"`):
  - ALL presentation actions (view, edit, grant, duplicate) are **forbidden** if
    the current time is outside the campaign window:
    `context.currentTime < resource.campaignStart || context.currentTime > resource.campaignEnd`.
- **Internal users** (`principal.job == Job::"internal"`) are EXEMPT from the
  campaign time window restriction and may access presentations at any time.
- Template actions are completely unaffected by campaign timing.

## Notes (Temporal Campaign)
- The forbid rule checks: non-internal job AND outside time window.
- Equivalently: `forbid ... when { principal.job != Job::"internal" && (context.currentTime < resource.campaignStart || context.currentTime > resource.campaignEnd) }`.
- All existing forbid rules (customer sharing, internal-only edit) still apply
  alongside the temporal restriction.
"""
        return MutationResult(schema=schema, policy_spec=spec)


class SalesFullExpansion(Mutation):
    def meta(self):
        return MutationMeta(
            id="sales_full_expansion",
            base_scenario="sales",
            difficulty="hard",
            description="Regional manager + template approval + presentation archive + delete combined",
            operators=["S9", "S1", "S1", "S7", "P1", "P1", "P2", "P2", "P5", "P7"],
            features_tested=["multi_mutation", "multi_forbid", "new_action", "complex_interaction"],
        )

    def apply(self, base_schema: str) -> MutationResult:
        schema = """\
// Sales Organization Permissions -- Cedar Schema (Full Expansion)

entity Job;
entity User in [Market] {
  job: Job,
  customerId: String,
  managedMarkets: Set<Market>,
};
entity Market;
entity Presentation {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  isArchived: Bool,
};
entity Template {
  owner: User,
  viewers: Set<User>,
  editors: Set<User>,
  viewerMarkets: Set<Market>,
  editorMarkets: Set<Market>,
  isApproved: Bool,
};
// Actions -- Presentations
action InternalPrezViewActions;
action ExternalPrezViewActions;
action PrezEditActions;
action viewPresentation, removeSelfAccessFromPresentation
    in [InternalPrezViewActions, ExternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action duplicatePresentation in [InternalPrezViewActions, PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action editPresentation in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
  };
action grantViewAccessToPresentation, grantEditAccessToPresentation
    in [PrezEditActions]
  appliesTo {
    principal: User,
    resource: Presentation,
    context: { target: User, },
  };
action deletePresentation appliesTo {
    principal: User,
    resource: Presentation,
  };

// Actions -- Templates
action InternalTemplateViewActions;
action MarketTemplateViewActions;
action TemplateEditActions;
action viewTemplate, duplicateTemplate
   in [InternalTemplateViewActions, TemplateEditActions,
       MarketTemplateViewActions]
  appliesTo {
    principal: User,
    resource: Template,
  };
action removeSelfAccessFromTemplate
   in [InternalTemplateViewActions, TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action editTemplate, removeOthersAccessToTemplate in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template
  };
action grantViewAccessToTemplate, grantEditAccessToTemplate
    in [TemplateEditActions]
  appliesTo {
    principal: User,
    resource: Template,
    context: { targetMarket?: Market, targetUser?: User },
  };
"""
        spec = """\
# Sales Organization Permissions -- Policy Specification (Full Expansion)

## Context

This policy governs access control for a sales organization platform with
Users, Markets, Presentations, Templates, and Jobs.

Users belong to Markets and have `job: Job`, `customerId: String`, and
`managedMarkets: Set<Market>`. Presentations have `isArchived: Bool`.
Templates have `isApproved: Bool`.

## Requirements

### 1. External Presentation View
- A user may perform **ExternalPrezViewActions** (viewPresentation,
  removeSelfAccessFromPresentation) if `principal in resource.viewers`.

### 2. Internal Presentation View
- A user may perform **InternalPrezViewActions** (viewPresentation,
  removeSelfAccessFromPresentation, duplicatePresentation) if
  `principal.job == Job::"internal"` AND `principal in resource.viewers`.

### 3. Presentation Edit
- A user may perform **PrezEditActions** if `resource.owner == principal` OR
  `principal in resource.editors`.

### 4. Customer Sharing Restriction (Deny Rule)
- **grantViewAccessToPresentation** is **forbidden** unless
  `context.target.job != Job::"customer"` OR
  (`principal.job == Job::"distributor"` AND
   `principal.customerId == context.target.customerId`).

### 5. Internal-Only Edit Sharing (Deny Rule)
- **grantEditAccessToPresentation** is **forbidden** when
  `context.target.job != Job::"internal"`.

### 6. Market Template View
- A user may perform **MarketTemplateViewActions** if `principal in resource.viewerMarkets`.

### 7. Internal Template View
- A user may perform **InternalTemplateViewActions** if
  `principal.job == Job::"internal"` AND `principal in resource.viewers`.

### 8. Template Edit
- A user may perform **TemplateEditActions** if `resource.owner == principal`
  OR `principal in resource.editors` OR `principal in resource.editorMarkets`.

### 9. Template View Grant Restriction (Deny Rule)
- **grantViewAccessToTemplate** is **forbidden** when `context has targetUser`
  AND `context.targetUser.job == Job::"customer"` AND the granting user is
  not a distributor sharing with their own customer.

### 10. Template Edit Grant Restriction (Deny Rule)
- **grantEditAccessToTemplate** is **forbidden** when
  `context has targetUser && context.targetUser.job != Job::"internal"`.

### 11. Delete Presentation (Owner Only)
- A new **deletePresentation** action is available on Presentations.
- ONLY the **owner** may delete: `resource.owner == principal`.
- The archive restriction does NOT block deletePresentation -- owners can
  delete archived presentations.

### 12. Archived Presentation Block (Deny Rule)
- If `resource.isArchived == true`, ALL **PrezEditActions** are **forbidden**
  on that presentation. This blocks editPresentation, grantViewAccessToPresentation,
  grantEditAccessToPresentation, and the edit-group variants.
- View actions and deletePresentation are NOT blocked by archive status.

### 13. Regional Manager Template Access
- A user with `job == Job::"regional_manager"` may perform **TemplateEditActions**
  on a template if any of the template's `editorMarkets` overlap with the
  user's `managedMarkets`.
- This is an additional path to template edit access alongside owner/editors/editorMarkets.

### 14. Unapproved Template Restriction (Deny Rule)
- If `resource.isApproved == false`, **TemplateEditActions** are **forbidden**
  for non-internal users (`principal.job != Job::"internal"`).
- Internal users (including regional managers with `Job::"regional_manager"`,
  who are considered internal for this purpose) are not affected.
  Note: if regional managers have their own Job type distinct from `Job::"internal"`,
  they ARE subject to this restriction. Only users with `job == Job::"internal"`
  bypass the approval gate.

## Notes
- This is a complex scenario with 5 forbid rules: customer sharing, internal-only
  edit, archive block, template approval, and template grant restrictions.
- Two new features: deletePresentation (owner-only) and regional manager template access.
- The archive block and approval gate are independent boolean-guarded forbids.
"""
        return MutationResult(schema=schema, policy_spec=spec)


# -- Registration --------------------------------------------------------------

MUTATIONS = [
    SalesRemoveCustomerRestriction(),
    SalesAddArchive(),
    SalesAddDelete(),
    SalesAddRegionalManager(),
    SalesAddApproval(),
    SalesAddTeam(),
    SalesTemporalCampaign(),
    SalesFullExpansion(),
]

for m in MUTATIONS:
    register(m)
