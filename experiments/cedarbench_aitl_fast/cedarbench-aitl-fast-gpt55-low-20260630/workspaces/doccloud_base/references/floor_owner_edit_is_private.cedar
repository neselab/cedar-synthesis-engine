permit (
    principal is User,
    action == Action::"EditIsPrivate",
    resource is Document
)
when {
    context.is_authenticated &&
    principal == resource.owner &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};