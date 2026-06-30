permit (
    principal is User,
    action == Action::"removeOthersAccessToTemplate",
    resource is Template
)
when {
    resource.owner == principal ||
    principal in resource.editors ||
    principal in resource.editorMarkets
};