// Floor: user with role "security_admin" must be permitted to perform action maskPII.
permit (
    principal is User,
    action == Action::"maskPII",
    resource is Order
)
when {
    principal.role == "security_admin"
};
