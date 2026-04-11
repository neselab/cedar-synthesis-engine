// Floor: User MUST write a Document in their own workspace.
permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.workspace == resource.workspace
};
