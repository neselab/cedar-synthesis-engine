permit (
    principal is User,
    action == Action::"add_triager",
    resource is Repository
)
when {
    !resource.isArchived &&
    principal in resource.admins
};