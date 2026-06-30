permit (
    principal is User,
    action == Action::"CreateGroup",
    resource is Drive
)
when {
    context.is_authenticated
};