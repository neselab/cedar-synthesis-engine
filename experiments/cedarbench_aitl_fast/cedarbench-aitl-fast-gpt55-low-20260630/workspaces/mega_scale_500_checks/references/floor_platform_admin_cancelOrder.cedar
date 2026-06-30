// Floor: user with role "platform_admin" must be permitted to perform action cancelOrder.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "platform_admin"
};
