permit (
    principal is User,
    action == Action::"merge_pr",
    resource is PullRequest
)
when { principal in resource.repo.writers && !resource.repo.isArchived };