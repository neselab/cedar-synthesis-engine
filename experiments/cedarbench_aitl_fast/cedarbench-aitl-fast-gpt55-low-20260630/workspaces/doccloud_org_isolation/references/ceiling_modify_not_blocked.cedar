permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    !(principal in resource.owner.blocked) &&
    !(resource.owner in principal.blocked)
};