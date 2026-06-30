permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
) when {
    principal in resource.viewerMarkets
};