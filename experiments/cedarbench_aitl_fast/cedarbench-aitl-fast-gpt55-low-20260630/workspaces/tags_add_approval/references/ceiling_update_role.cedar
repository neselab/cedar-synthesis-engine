permit (
    principal is User,
    action == Action::"UpdateWorkspace",
    resource is Workspace
)
when {
    principal in Role::"role-a" &&
    resource.isApproved
};