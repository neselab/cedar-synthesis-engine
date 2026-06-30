permit (
    principal is User,
    action == Action::"approve_pr",
    resource is PullRequest
)
when {
    principal != resource.author &&
    (principal in resource.repo.readers ||
     principal in resource.repo.triagers ||
     principal in resource.repo.contributors ||
     principal in resource.repo.writers ||
     principal in resource.repo.maintainers ||
     principal in resource.repo.admins)
};