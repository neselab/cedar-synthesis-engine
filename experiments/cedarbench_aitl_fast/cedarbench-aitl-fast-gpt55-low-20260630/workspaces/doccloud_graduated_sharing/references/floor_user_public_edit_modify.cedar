permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    resource.publicAccess == "edit" &&
    !(principal in resource.owner.blocked) &&
    !(resource.owner in principal.blocked)
};