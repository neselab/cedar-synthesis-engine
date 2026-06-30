permit (
    principal is User,
    action == Action::"add_writer",
    resource is Repository
)
when {
    principal in resource.admins &&
    !resource.isArchived &&
    resource.collaboratorCount < resource.maxCollaborators
};