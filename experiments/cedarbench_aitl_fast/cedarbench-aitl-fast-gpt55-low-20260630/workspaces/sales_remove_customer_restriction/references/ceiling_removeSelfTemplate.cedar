permit (
    principal is User,
    action == Action::"removeSelfAccessFromTemplate",
    resource is Template
) when {
    (principal.job == Job::"internal" && principal in resource.viewers) ||
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets
};