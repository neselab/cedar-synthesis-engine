permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal.job == Job::"internal" &&
    principal in resource.editorMarkets
};