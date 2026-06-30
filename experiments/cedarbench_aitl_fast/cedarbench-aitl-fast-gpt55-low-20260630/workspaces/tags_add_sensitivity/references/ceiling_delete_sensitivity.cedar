permit (
    principal is User,
    action == Action::"DeleteWorkspace",
    resource is Workspace
)
when {
    resource.sensitivity <= 3
};