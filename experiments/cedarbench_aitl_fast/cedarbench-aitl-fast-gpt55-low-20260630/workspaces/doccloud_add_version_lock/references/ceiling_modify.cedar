permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    !resource.isLocked &&
    (
        principal == resource.owner ||
        principal in resource.modifyACL ||
        resource.publicAccess == "edit"
    )
};