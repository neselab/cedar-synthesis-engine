// Floor: user with role "security_basic" must be permitted to perform action cancelOrder.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "security_basic"
};
