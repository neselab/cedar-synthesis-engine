permit (
    principal is User,
    action == Action::"UpdateWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-A" &&
    principal.allowedTagsForRole has "Role-A" &&
    principal.allowedTagsForRole["Role-A"] has production_status &&
    principal.allowedTagsForRole["Role-A"]["production_status"].contains("ALL") &&
    !(resource.tags has country) &&
    !(resource.tags has stage)
};