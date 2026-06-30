permit (
    principal is User,
    action == Action::"UpdateWorkspace",
    resource is Workspace
)
when {
    resource.isApproved
};