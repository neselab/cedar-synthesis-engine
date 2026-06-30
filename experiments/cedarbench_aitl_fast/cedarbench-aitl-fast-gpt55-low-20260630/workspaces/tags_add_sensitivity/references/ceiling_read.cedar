permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
)
when {
    principal in Role::"Role-A" ||
    principal in Role::"Role-B"
};