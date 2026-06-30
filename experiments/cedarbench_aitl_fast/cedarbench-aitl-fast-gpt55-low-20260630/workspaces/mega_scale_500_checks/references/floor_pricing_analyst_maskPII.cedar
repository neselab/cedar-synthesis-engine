// Floor: user with role "pricing_analyst" must be permitted to perform action maskPII.
permit (
    principal is User,
    action == Action::"maskPII",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
