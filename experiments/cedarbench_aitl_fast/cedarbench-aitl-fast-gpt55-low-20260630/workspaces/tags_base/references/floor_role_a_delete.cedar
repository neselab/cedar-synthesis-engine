permit (
    principal is User,
    action == Action::"DeleteWorkspace",
    resource is Workspace
)
when {
    principal in Role::"Role-A" &&
    principal.allowedTagsForRole has "Role-A" &&
    !(principal.allowedTagsForRole["Role-A"] has production_status) &&
    !(principal.allowedTagsForRole["Role-A"] has country) &&
    !(principal.allowedTagsForRole["Role-A"] has stage) &&
    !(resource.tags has production_status) &&
    !(resource.tags has country) &&
    !(resource.tags has stage)
};