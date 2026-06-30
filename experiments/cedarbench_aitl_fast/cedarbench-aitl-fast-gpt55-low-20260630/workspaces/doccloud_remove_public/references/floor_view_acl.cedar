permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    context.is_authenticated &&
    principal in resource.viewACL &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};