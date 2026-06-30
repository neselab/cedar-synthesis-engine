permit (
    principal is User,
    action == Action::"assign_issue",
    resource is Issue
)
when {
    principal in resource.repo.triagers ||
    principal in resource.repo.writers ||
    principal in resource.repo.maintainers ||
    principal in resource.repo.admins
};