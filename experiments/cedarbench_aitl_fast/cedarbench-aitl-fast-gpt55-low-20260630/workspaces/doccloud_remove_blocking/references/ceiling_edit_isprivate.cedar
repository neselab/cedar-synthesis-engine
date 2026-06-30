permit (
    principal is User,
    action == Action::"EditIsPrivate",
    resource is Document
) when {
    context.is_authenticated &&
    (principal == resource.owner ||
     principal in resource.manageACL)
};