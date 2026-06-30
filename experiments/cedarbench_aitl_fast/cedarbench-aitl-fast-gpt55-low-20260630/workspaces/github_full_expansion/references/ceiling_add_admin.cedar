permit (
    principal is User,
    action == Action::"add_admin",
    resource is Repository
)
when {
    !resource.isArchived &&
    principal in resource.admins
};