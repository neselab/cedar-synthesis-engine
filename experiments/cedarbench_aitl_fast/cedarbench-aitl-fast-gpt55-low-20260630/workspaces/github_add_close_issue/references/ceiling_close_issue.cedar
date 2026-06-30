// Ceiling: close_issue — reporter+reader OR writer can close
permit (
    principal is User,
    action == Action::"close_issue",
    resource is Issue
) when {
    (principal in resource.repo.readers && principal == resource.reporter) ||
    principal in resource.repo.writers
};
