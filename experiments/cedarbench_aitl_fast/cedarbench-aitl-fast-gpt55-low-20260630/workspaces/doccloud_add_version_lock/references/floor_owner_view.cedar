permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    principal == resource.owner &&
    !resource.owner.blocked.contains(principal) &&
    !principal.blocked.contains(resource.owner)
};