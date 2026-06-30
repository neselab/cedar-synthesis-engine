permit (
    principal is User,
    action == Action::"read",
    resource is Doc
)
when {
    principal.role == "admin" || resource.tier == 1
};