forbid (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    resource.owner.blocked.contains(principal)
};