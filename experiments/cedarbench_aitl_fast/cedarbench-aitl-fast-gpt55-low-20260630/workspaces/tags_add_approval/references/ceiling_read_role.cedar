permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
)
when {
    principal in Role::"role-a" ||
    principal in Role::"role-b"
};