// Floor: the owner MUST be permitted to read their own document.
permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    principal == resource.owner
};
