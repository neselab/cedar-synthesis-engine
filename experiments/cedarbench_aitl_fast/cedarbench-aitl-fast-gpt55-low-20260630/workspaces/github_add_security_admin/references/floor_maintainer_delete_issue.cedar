permit (
    principal is User,
    action == Action::"delete_issue",
    resource is Issue
)
when { principal in resource.repo.maintainers };
