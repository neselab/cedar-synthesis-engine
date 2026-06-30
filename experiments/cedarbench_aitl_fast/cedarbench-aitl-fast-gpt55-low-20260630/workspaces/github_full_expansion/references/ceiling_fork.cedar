permit (
    principal is User,
    action == Action::"fork",
    resource is Repository
)
when {
    !resource.isPrivate &&
    (principal in resource.readers ||
     principal in resource.triagers ||
     principal in resource.contributors ||
     principal in resource.writers ||
     principal in resource.maintainers ||
     principal in resource.admins)
};