permit (
    principal is User,
    action == Action::"viewTemplate",
    resource is Template
)
when {
    resource.owner == principal ||
    principal in resource.viewers ||
    principal in resource.editors ||
    principal in resource.viewerMarkets ||
    principal in resource.editorMarkets
};