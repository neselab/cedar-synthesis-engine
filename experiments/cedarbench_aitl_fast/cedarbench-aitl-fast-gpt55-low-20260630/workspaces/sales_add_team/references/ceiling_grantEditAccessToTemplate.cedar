permit (
    principal is User,
    action == Action::"grantEditAccessToTemplate",
    resource is Template
)
when {
    (resource.owner == principal ||
     principal in resource.editors ||
     principal in resource.editorMarkets) &&
    (!(context has targetUser) ||
     (context has targetUser &&
      context.targetUser.job == Job::"internal"))
};