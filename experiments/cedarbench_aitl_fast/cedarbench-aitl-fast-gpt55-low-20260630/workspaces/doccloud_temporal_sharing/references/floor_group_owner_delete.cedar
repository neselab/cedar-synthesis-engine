permit (
    principal is User,
    action == Action::"DeleteGroup",
    resource is Group
)
when {
    principal == resource.owner &&
    context.is_authenticated
};