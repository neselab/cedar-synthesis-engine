// Floor: a cs_agent MUST be permitted to listOrders an order with status=shipped.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "cs_agent"
    && resource.status == "shipped"
};
