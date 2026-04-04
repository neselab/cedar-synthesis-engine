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
