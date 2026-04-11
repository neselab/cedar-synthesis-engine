// Floor: a security_admin MUST be permitted to listOrders an order with status=shipped.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "security_admin"
    && resource.status == "shipped"
};
