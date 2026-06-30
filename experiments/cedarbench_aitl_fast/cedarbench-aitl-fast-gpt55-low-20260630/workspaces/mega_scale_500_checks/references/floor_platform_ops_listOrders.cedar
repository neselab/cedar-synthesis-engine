// Floor: user with role "platform_ops" must be permitted to perform action listOrders.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "platform_ops"
};
