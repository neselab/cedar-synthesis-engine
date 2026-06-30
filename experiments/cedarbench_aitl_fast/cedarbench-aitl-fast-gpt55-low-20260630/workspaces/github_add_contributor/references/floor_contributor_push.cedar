permit (
    principal is User,
    action == Action::"push",
    resource is Repository
)
when {
    principal in resource.contributors &&
    resource.isArchived == false
};