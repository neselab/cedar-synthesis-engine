permit (
    principal is Public,
    action == Action::"ViewMetadata",
    resource is Document
)
when {
    resource.publicAccess == "preview" ||
    resource.publicAccess == "view" ||
    resource.publicAccess == "edit"
};