permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    resource.isPrivate == false &&
    (resource.publicAccess == "view" || resource.publicAccess == "edit")
};