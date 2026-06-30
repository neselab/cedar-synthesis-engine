permit (
    principal is User,
    action == Action::"add_triager",
    resource is Repository
) when {
    principal in resource.admins
};