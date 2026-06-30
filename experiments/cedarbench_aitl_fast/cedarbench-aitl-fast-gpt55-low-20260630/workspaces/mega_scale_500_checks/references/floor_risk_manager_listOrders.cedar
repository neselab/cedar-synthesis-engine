// Floor: user with role "risk_manager" must be permitted to perform action listOrders.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "risk_manager"
};
