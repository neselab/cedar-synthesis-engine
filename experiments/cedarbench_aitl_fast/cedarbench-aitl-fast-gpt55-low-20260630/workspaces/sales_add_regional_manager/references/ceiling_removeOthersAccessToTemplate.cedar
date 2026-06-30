permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets ||
    (principal.job == Job::"regional_manager" && resource.editorMarkets.containsAny(principal.managedMarkets))
};