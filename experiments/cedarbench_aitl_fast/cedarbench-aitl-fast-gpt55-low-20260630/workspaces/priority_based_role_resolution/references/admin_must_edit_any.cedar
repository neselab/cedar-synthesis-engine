// Floor: a User holding the "admin" role MUST be permitted to
// editRecord on any Record, regardless of tier.
permit (
    principal is User,
    action == Action::"editRecord",
    resource is Record
)
when {
    principal.roles.contains("admin")
};
