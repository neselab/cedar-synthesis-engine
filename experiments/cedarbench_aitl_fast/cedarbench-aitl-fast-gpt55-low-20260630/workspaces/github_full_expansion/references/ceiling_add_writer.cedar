permit (
    principal is User,
    action == Action::"add_writer",
    resource is Repository
)
when {
    !resource.isArchived &&
    principal in resource.admins
};