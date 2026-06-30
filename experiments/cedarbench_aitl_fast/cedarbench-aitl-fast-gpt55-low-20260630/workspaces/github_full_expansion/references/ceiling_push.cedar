permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when {
    !resource.isArchived &&
    (principal in resource.contributors ||
     principal in resource.writers ||
     principal in resource.maintainers ||
     principal in resource.admins)
};