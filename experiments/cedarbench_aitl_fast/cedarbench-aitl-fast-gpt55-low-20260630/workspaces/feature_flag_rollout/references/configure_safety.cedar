// Ceiling: configure permitted only when role is admin.
permit (
    principal is User,
    action == Action::"configure",
    resource is Feature
)
when {
    principal.role == "admin"
};
