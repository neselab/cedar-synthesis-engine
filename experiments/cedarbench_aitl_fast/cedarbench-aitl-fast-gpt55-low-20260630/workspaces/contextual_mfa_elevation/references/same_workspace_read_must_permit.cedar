// Floor: User MUST read a Document in their own workspace.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.workspace == resource.workspace
};
