permit (
    principal is User,
    action == Action::"merge_pr",
    resource is PullRequest
)
when {
    !resource.repo.isArchived &&
    (principal in resource.repo.writers ||
     principal in resource.repo.maintainers ||
     principal in resource.repo.admins)
};