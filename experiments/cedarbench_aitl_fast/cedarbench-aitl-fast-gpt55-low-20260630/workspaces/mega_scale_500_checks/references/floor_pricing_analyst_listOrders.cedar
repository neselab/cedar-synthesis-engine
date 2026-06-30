// Floor: user with role "pricing_analyst" must be permitted to perform action listOrders.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
