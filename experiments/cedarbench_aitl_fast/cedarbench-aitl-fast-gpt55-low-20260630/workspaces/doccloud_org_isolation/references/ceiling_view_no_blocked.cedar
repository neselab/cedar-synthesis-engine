permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    !(principal in resource.owner.blocked) &&
    !(resource.owner in principal.blocked)
};