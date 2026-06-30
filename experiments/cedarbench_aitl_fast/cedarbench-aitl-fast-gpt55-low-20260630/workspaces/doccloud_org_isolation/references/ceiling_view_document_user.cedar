permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
)
when {
    context.is_authenticated &&
    (principal == resource.owner ||
     principal in resource.viewACL ||
     principal in resource.manageACL ||
     resource.publicAccess == "view" ||
     resource.publicAccess == "edit")
};