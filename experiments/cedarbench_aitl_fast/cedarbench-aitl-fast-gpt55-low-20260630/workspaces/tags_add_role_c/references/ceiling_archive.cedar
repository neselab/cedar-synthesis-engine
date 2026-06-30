permit (
    principal is User,
    action == Action::"ArchiveWorkspace",
    resource is Workspace
) when {
    principal in Role::"Role-C"
};