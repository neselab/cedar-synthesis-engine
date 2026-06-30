permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    principal in resource.editorMarkets
};