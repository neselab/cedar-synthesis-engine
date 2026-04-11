// Ceiling: read permitted only when same workspace.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.workspace == resource.workspace
};
