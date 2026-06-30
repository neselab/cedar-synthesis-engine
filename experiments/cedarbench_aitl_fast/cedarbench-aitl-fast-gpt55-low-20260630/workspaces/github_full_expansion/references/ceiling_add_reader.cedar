permit (
    principal is User,
    action == Action::"add_reader",
    resource is Repository
)
when {
    !resource.isArchived &&
    principal in resource.admins
};