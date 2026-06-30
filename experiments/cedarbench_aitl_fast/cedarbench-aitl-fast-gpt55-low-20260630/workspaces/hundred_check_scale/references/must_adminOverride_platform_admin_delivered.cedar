// Floor: a platform_admin MUST be permitted to adminOverride an order with status=delivered.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "platform_admin"
    && resource.status == "delivered"
};
