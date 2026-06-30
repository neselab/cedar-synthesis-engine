permit (
    principal is User,
    action == Action::"CreateDocument",
    resource is Drive
)
when {
    context.is_authenticated
};