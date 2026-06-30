permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    principal == resource.owner &&
    context.is_authenticated &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};