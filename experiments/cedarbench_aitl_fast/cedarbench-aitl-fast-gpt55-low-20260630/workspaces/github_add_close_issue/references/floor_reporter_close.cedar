// Floor: A reader who is the reporter MUST be able to close their own issue
// (Ensures the reporter self-close path works even without writer role)
permit (
    principal is User,
    action == Action::"close_issue",
    resource is Issue
) when {
    principal in resource.repo.readers &&
    principal == resource.reporter &&
    !(principal in resource.repo.writers)
};
