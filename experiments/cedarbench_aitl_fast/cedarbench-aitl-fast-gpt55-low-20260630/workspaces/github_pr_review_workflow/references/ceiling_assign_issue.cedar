permit (
    principal is User,
    action == Action::"assign_issue",
    resource is Issue
)
when { principal in resource.repo.triagers };