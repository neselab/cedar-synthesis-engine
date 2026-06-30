// Floor: user with role "risk_analyst" must be permitted to perform action maskPII.
permit (
    principal is User,
    action == Action::"maskPII",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
