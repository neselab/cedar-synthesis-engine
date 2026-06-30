permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when {
    (principal in resource.contributors || principal in resource.writers) &&
    resource.isArchived == false
};