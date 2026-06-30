permit (
    principal is User,
    action == Action::"request_changes",
    resource is PullRequest
)
when { principal in resource.repo.readers && !(principal == resource.author) };