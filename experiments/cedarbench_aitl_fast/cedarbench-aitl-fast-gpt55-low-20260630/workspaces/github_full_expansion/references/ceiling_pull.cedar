permit (
    principal is User,
    action == Action::"pull",
    resource is Repository
)
when {
    principal in resource.readers ||
    principal in resource.triagers ||
    principal in resource.contributors ||
    principal in resource.writers ||
    principal in resource.maintainers ||
    principal in resource.admins
};