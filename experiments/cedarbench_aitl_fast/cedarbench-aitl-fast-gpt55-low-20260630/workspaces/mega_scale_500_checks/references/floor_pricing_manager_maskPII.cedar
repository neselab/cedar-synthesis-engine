// Floor: user with role "pricing_manager" must be permitted to perform action maskPII.
permit (
    principal is User,
    action == Action::"maskPII",
    resource is Order
)
when {
    principal.role == "pricing_manager"
};
