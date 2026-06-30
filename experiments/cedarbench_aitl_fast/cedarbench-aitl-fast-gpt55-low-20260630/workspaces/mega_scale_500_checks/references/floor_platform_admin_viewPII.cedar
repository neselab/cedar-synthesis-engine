// Floor: user with role "platform_admin" must be permitted to perform action viewPII.
permit (
    principal is User,
    action == Action::"viewPII",
    resource is Order
)
when {
    principal.role == "platform_admin"
};
