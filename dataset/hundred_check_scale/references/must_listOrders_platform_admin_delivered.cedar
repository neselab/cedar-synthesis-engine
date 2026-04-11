// Floor: a platform_admin MUST be permitted to listOrders an order with status=delivered.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "platform_admin"
    && resource.status == "delivered"
};
