permit (
    principal is User,
    action == Action::"approve_pr",
    resource is PullRequest
)
when { principal in resource.repo.readers && !(principal == resource.author) };