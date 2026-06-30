permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    (principal.job == Job::"internal" && principal in resource.viewers) ||
    principal in resource.viewerMarkets ||
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets ||
    (principal.job == Job::"regional_manager" && resource.editorMarkets.containsAny(principal.managedMarkets))
};