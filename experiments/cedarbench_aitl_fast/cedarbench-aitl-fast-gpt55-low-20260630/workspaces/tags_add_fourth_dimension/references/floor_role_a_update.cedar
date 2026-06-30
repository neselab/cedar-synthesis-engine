permit (
    principal is User,
    action == Action::"UpdateWorkspace",
    resource is Workspace
)
when {
    principal in Role::"role-a" &&
    principal.allowedTagsForRole has "Role-A" &&
    principal.allowedTagsForRole["Role-A"] has production_status &&
    principal.allowedTagsForRole["Role-A"].production_status.contains("ALL") &&
    principal.allowedTagsForRole["Role-A"] has country &&
    principal.allowedTagsForRole["Role-A"].country.contains("ALL") &&
    principal.allowedTagsForRole["Role-A"] has stage &&
    principal.allowedTagsForRole["Role-A"].stage.contains("ALL") &&
    principal.allowedTagsForRole["Role-A"] has department &&
    principal.allowedTagsForRole["Role-A"].department.contains("ALL")
};