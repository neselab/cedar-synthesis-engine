permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    context.is_authenticated == true &&
    principal in resource.viewACL &&
    !resource.owner.blocked.contains(principal) &&
    !principal.blocked.contains(resource.owner) &&
    context.currentTime <= resource.expiryDate
};