// Floor: user with role "pricing_manager" must be permitted to perform action viewPII.
permit (
    principal is User,
    action == Action::"viewPII",
    resource is Order
)
when {
    principal.role == "pricing_manager"
};
