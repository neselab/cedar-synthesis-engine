permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    principal in resource.modifyACL &&
    !(principal in resource.owner.blocked) &&
    !(resource.owner in principal.blocked)
};