permit (
    principal is User,
    action == Action::"close_issue",
    resource is Issue
)
when {
    (principal in resource.repo.readers && principal == resource.reporter) ||
    principal in resource.repo.writers ||
    principal in resource.repo.maintainers ||
    principal in resource.repo.admins
};