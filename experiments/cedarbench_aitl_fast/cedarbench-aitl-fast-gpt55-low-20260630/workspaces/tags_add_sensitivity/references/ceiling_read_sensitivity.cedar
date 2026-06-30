permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
)
when {
    (principal in Role::"Role-A" && resource.sensitivity <= 3) ||
    (principal in Role::"Role-B" && resource.sensitivity <= 1)
};