// Ceiling: comment permitted only when same workspace.
permit (
    principal is User,
    action == Action::"comment",
    resource is Document
)
when {
    principal.workspace == resource.workspace
};
