// Floor: user with role "risk_analyst" must be permitted to perform action cancelOrder.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
