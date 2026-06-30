permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    principal == resource.owner &&
    !resource.isLocked &&
    !resource.owner.blocked.contains(principal) &&
    !principal.blocked.contains(resource.owner)
};