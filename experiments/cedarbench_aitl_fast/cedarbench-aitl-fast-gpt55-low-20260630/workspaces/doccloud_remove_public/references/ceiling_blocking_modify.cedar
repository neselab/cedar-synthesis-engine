permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};