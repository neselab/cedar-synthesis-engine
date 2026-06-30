permit (
    principal is User,
    action == Action::"add_maintainer",
    resource is Repository
)
when {
    !resource.isArchived &&
    principal in resource.admins
};