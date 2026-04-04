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
