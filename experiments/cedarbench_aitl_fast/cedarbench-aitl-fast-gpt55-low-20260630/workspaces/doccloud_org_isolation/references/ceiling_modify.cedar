permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    (
        principal == resource.owner ||
        principal in resource.modifyACL ||
        principal in resource.manageACL ||
        resource.publicAccess == "edit"
    )
};