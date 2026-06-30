// Floor: user with role "risk_analyst" must be permitted to perform action adminOverride.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
