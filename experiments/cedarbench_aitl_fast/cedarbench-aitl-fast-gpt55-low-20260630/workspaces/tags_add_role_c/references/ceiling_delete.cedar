permit (
    principal is User,
    action == Action::"DeleteWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-A"
};