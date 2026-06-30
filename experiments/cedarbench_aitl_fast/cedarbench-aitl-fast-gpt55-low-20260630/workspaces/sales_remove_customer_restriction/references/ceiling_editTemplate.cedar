permit (
    principal is User,
    action == Action::"editTemplate",
    resource is Template
) when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets
};