permit (
    principal is User,
    action == Action::"ReadWorkspace",
    resource is Workspace
) when {
    principal == resource.owner
};