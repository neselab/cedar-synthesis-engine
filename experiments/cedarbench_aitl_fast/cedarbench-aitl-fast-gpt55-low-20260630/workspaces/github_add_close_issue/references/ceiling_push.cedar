// Ceiling: push — writers can push, but NOT if repo is archived
permit (
    principal is User,
    action == Action::"push",
    resource is Repository
) when {
    principal in resource.writers &&
    !resource.isArchived
};
