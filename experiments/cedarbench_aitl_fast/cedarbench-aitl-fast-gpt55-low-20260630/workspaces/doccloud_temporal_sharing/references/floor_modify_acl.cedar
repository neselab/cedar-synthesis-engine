permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    principal in resource.modifyACL &&
    context.is_authenticated &&
    context.requestTime <= resource.shareExpiry &&
    !resource.isLocked &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};