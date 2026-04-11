// Floor: a cs_manager MUST be permitted to listOrders an order with status=cart.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "cs_manager"
    && resource.status == "cart"
};
