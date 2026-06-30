permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    principal in resource.viewACL &&
    context.is_authenticated &&
    context.requestTime <= resource.shareExpiry &&
    !principal.blocked.contains(resource.owner) &&
    !resource.owner.blocked.contains(principal)
};