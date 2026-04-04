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
