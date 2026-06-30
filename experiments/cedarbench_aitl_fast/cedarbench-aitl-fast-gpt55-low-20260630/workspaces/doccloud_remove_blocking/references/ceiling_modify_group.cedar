permit (
    principal is User,
    action == Action::"ModifyGroup",
    resource is Group
) when {
    context.is_authenticated &&
    principal == resource.owner
};