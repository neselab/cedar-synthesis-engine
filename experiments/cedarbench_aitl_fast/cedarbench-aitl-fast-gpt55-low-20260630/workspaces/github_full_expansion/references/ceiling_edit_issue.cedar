permit (
    principal is User,
    action == Action::"edit_issue",
    resource is Issue
)
when {
    !resource.isLocked &&
    ((principal in resource.repo.readers && principal == resource.reporter) ||
     principal in resource.repo.writers ||
     principal in resource.repo.maintainers ||
     principal in resource.repo.admins)
};