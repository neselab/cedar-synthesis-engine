permit (
    principal is User,
    action == Action::"DeleteDocument",
    resource is Document
)
when {
    principal == resource.owner &&
    context.is_authenticated
};