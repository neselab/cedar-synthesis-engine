permit (
    principal is User,
    action == Action::"edit_issue",
    resource is Issue
)
when { (principal in resource.repo.readers && principal == resource.reporter) || principal in resource.repo.writers };