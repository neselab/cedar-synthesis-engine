permit (
    principal is User,
    action == Action::"DeleteGroup",
    resource is Group
) when {
    context.is_authenticated == true &&
    principal == resource.owner
};