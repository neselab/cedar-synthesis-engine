permit (
    principal is User,
    action == Action::"DeleteWorkspace",
    resource is Workspace
)
when {
    principal in Role::"Role-A" &&
    resource.sensitivity <= 3 &&
    principal.allowedTagsForRole has "Role-A" &&
    principal.allowedTagsForRole["Role-A"] has production_status &&
    principal.allowedTagsForRole["Role-A"].production_status.contains("ALL")
};