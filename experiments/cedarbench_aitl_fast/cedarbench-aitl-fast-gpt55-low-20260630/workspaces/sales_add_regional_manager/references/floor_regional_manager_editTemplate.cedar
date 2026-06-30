permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job == Job::"regional_manager" &&
    resource.editorMarkets.containsAny(principal.managedMarkets)
};