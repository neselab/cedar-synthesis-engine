permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    principal in resource.viewACL &&
    principal.org == resource.owner.org &&
    !(principal in resource.owner.blocked) &&
    !(resource.owner in principal.blocked)
};