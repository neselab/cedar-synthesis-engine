permit (
    principal is User,
    action == Action::"ViewMetadata",
    resource is Document
)
when {
    context.is_authenticated &&
    (
        principal == resource.owner ||
        principal in resource.viewACL ||
        principal in resource.modifyACL ||
        principal in resource.manageACL ||
        resource.publicAccess == "preview" ||
        resource.publicAccess == "view" ||
        resource.publicAccess == "edit"
    )
};