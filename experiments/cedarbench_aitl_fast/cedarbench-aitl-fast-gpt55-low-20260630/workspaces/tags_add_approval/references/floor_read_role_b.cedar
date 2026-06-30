permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
)
when {
    principal in Role::"role-b" &&
    principal.allowedTagsForRole has "Role-B" &&
    principal.allowedTagsForRole["Role-B"] has production_status &&
    principal.allowedTagsForRole["Role-B"].production_status.contains("ALL") &&
    principal.allowedTagsForRole["Role-B"] has country &&
    principal.allowedTagsForRole["Role-B"].country.contains("ALL") &&
    principal.allowedTagsForRole["Role-B"] has stage &&
    principal.allowedTagsForRole["Role-B"].stage.contains("ALL")
};