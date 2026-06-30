// Floor: user with role "cs_manager" must be permitted to perform action viewPII.
permit (
    principal is User,
    action == Action::"viewPII",
    resource is Order
)
when {
    principal.role == "cs_manager"
};
