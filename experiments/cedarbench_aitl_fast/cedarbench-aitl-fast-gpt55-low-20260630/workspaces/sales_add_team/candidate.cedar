permit (
  principal is User,
  action in Action::"ExternalPrezViewActions",
  resource is Presentation
)
when {
  principal in resource.viewers ||
  principal in resource.viewerTeams
};

permit (
  principal is User,
  action in Action::"InternalPrezViewActions",
  resource is Presentation
)
when {
  principal.job == Job::"internal" &&
  principal in resource.viewers
};

permit (
  principal is User,
  action in Action::"PrezEditActions",
  resource is Presentation
)
when {
  resource.owner == principal ||
  principal in resource.editors ||
  principal in resource.editorTeams
};

forbid (
  principal is User,
  action == Action::"grantViewAccessToPresentation",
  resource is Presentation
)
when {
  context.target.job == Job::"customer"
}
unless {
  principal.job == Job::"distributor" &&
  principal.customerId == context.target.customerId
};

forbid (
  principal is User,
  action == Action::"grantEditAccessToPresentation",
  resource is Presentation
)
when {
  context.target.job != Job::"internal"
};

permit (
  principal is User,
  action in Action::"MarketTemplateViewActions",
  resource is Template
)
when {
  principal in resource.viewerMarkets
};

permit (
  principal is User,
  action in Action::"InternalTemplateViewActions",
  resource is Template
)
when {
  principal.job == Job::"internal" &&
  principal in resource.viewers
};

permit (
  principal is User,
  action in Action::"TemplateEditActions",
  resource is Template
)
when {
  resource.owner == principal ||
  principal in resource.editors ||
  principal in resource.editorMarkets
};

forbid (
  principal is User,
  action == Action::"grantViewAccessToTemplate",
  resource is Template
)
when {
  context has targetUser &&
  context.targetUser.job == Job::"customer"
}
unless {
  principal.job == Job::"distributor" &&
  principal.customerId == context.targetUser.customerId
};

forbid (
  principal is User,
  action == Action::"grantEditAccessToTemplate",
  resource is Template
)
when {
  context has targetUser &&
  context.targetUser.job != Job::"internal"
};