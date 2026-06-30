permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    (principal.groupA && resource.category == "alpha") ||
    (principal.groupB && resource.category == "beta")
};