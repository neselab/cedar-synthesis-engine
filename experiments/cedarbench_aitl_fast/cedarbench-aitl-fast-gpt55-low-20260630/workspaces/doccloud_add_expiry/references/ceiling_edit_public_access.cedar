permit (
    principal is User,
    action == Action::"EditPublicAccess",
    resource is Document
) when {
    context.is_authenticated == true &&
    (principal == resource.owner ||
     principal in resource.manageACL)
};