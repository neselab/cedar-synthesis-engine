// Floor: a returns MUST be permitted to listOrders an order with status=delivered.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "returns"
    && resource.status == "delivered"
};
