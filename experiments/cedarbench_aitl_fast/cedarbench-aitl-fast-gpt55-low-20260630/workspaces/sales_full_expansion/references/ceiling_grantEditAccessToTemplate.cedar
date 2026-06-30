permit (
    principal is User,
    action == Action::"grantEditAccessToTemplate",
    resource is Template
) when {
    (resource.owner == principal ||
     principal in resource.editors ||
     principal in resource.editorMarkets ||
     (principal.job == Job::"regional_manager" && resource.editorMarkets.containsAny(principal.managedMarkets))) &&
    (resource.isApproved == true || principal.job == Job::"internal") &&
    (!(context has targetUser) ||
     (context has targetUser && context.targetUser.job == Job::"internal"))
};