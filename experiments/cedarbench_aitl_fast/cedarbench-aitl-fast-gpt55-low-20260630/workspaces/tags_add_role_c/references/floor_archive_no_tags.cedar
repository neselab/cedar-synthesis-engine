permit (
    principal is User,
    action == Action::"ArchiveWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-C" &&
    principal.allowedTagsForRole has "Role-C" &&
    !(principal.allowedTagsForRole["Role-C"] has production_status) &&
    !(principal.allowedTagsForRole["Role-C"] has country) &&
    !(principal.allowedTagsForRole["Role-C"] has stage) &&
    !(resource.tags has production_status) &&
    !(resource.tags has country) &&
    !(resource.tags has stage)
};