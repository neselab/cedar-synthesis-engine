permit (
    principal is User,
    action == Action::"edit_issue",
    resource is Issue
)
when {
    !resource.isLocked &&
    (principal in resource.repo.writers ||
     (principal in resource.repo.readers && principal == resource.reporter))
};