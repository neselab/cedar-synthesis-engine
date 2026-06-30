permit (
    principal is Public,
    action == Action::"ViewMetadata",
    resource is Document
)
when {
    resource.publicAccess == "preview"
};