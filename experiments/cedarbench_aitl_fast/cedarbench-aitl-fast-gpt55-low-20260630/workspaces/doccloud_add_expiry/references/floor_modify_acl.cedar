permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    context.is_authenticated == true &&
    principal in resource.modifyACL &&
    !resource.owner.blocked.contains(principal) &&
    !principal.blocked.contains(resource.owner) &&
    context.currentTime <= resource.expiryDate
};