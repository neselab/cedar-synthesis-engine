permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    principal == resource.owner &&
    context.is_authenticated &&
    !resource.isLocked &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};