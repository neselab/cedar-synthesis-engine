permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
)
when {
    principal in Role::"Role-B" &&
    resource.sensitivity <= 1 &&
    principal.allowedTagsForRole has "Role-B" &&
    principal.allowedTagsForRole["Role-B"] has production_status &&
    principal.allowedTagsForRole["Role-B"].production_status.contains("ALL")
};