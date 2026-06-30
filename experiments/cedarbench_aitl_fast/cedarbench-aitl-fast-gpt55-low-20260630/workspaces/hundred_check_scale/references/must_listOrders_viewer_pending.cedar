// Floor: a viewer MUST be permitted to listOrders an order with status=pending.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "viewer"
    && resource.status == "pending"
};
