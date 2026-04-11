// Ceiling: write permitted only when same workspace.
permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.workspace == resource.workspace
};
