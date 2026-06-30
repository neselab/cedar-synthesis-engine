// Floor: user with role "risk_analyst" must be permitted to perform action viewPII.
permit (
    principal is User,
    action == Action::"viewPII",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
