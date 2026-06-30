permit (
  principal,
  action in Action::"ExternalPrezViewActions",
  resource
)
when {
  principal is User &&
  resource is Presentation &&
  principal in resource.viewers
};

permit (
  principal,
  action in Action::"InternalPrezViewActions",
  resource
)
when {
  principal is User &&
  resource is Presentation &&
  principal.job == Job::"internal" &&
  principal in resource.viewers
};

permit (
  principal,
  action in Action::"PrezEditActions",
  resource
)
when {
  principal is User &&
  resource is Presentation &&
  (resource.owner == principal || principal in resource.editors)
};

permit (
  principal,
  action == Action::"deletePresentation",
  resource
)
when {
  principal is User &&
  resource is Presentation &&
  resource.owner == principal
};

forbid (
  principal,
  action == Action::"editPresentation",
  resource
)
when {
  principal is User &&
  resource is Presentation &&
  resource.isArchived
};

forbid (
  principal,
  action == Action::"grantViewAccessToPresentation",
  resource
)
when {
  principal is User &&
  resource is Presentation &&
  resource.isArchived
};

forbid (
  principal,
  action == Action::"grantEditAccessToPresentation",
  resource
)
when {
  principal is User &&
  resource is Presentation &&
  resource.isArchived
};

forbid (
  principal,
  action == Action::"grantViewAccessToPresentation",
  resource
)
unless {
  context.target.job != Job::"customer" ||
  (
    principal.job == Job::"distributor" &&
    principal.customerId == context.target.customerId
  )
};

forbid (
  principal,
  action == Action::"grantEditAccessToPresentation",
  resource
)
when {
  context.target.job != Job::"internal"
};

permit (
  principal,
  action in Action::"MarketTemplateViewActions",
  resource
)
when {
  principal is User &&
  resource is Template &&
  principal in resource.viewerMarkets
};

permit (
  principal,
  action in Action::"InternalTemplateViewActions",
  resource
)
when {
  principal is User &&
  resource is Template &&
  principal.job == Job::"internal" &&
  principal in resource.viewers
};

permit (
  principal,
  action in Action::"TemplateEditActions",
  resource
)
when {
  principal is User &&
  resource is Template &&
  (
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets
  )
};

permit (
  principal,
  action in Action::"TemplateEditActions",
  resource
)
when {
  principal is User &&
  resource is Template &&
  principal.job == Job::"regional_manager" &&
  resource.editorMarkets.containsAny(principal.managedMarkets)
};

forbid (
  principal,
  action == Action::"editTemplate",
  resource
)
when {
  principal is User &&
  resource is Template &&
  resource.isApproved == false &&
  principal.job != Job::"internal"
};

forbid (
  principal,
  action == Action::"removeOthersAccessToTemplate",
  resource
)
when {
  principal is User &&
  resource is Template &&
  resource.isApproved == false &&
  principal.job != Job::"internal"
};

forbid (
  principal,
  action == Action::"grantViewAccessToTemplate",
  resource
)
when {
  principal is User &&
  resource is Template &&
  resource.isApproved == false &&
  principal.job != Job::"internal"
};

forbid (
  principal,
  action == Action::"grantEditAccessToTemplate",
  resource
)
when {
  principal is User &&
  resource is Template &&
  resource.isApproved == false &&
  principal.job != Job::"internal"
};

forbid (
  principal,
  action == Action::"grantViewAccessToTemplate",
  resource
)
when {
  context has targetUser &&
  context.targetUser.job == Job::"customer" &&
  !(
    principal.job == Job::"distributor" &&
    principal.customerId == context.targetUser.customerId
  )
};

forbid (
  principal,
  action == Action::"grantEditAccessToTemplate",
  resource
)
when {
  context has targetUser &&
  context.targetUser.job != Job::"internal"
};