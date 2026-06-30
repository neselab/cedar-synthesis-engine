permit (
    principal is User,
    action == Action::"AddToShareACL",
    resource is Document
) when {
    context.is_authenticated &&
    (principal == resource.owner || principal in resource.manageACL)
};