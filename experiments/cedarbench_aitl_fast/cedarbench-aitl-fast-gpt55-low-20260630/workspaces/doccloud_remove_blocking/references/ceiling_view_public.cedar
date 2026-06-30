permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
) when {
    resource.publicAccess == "view" ||
    resource.publicAccess == "edit"
};