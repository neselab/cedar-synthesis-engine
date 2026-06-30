// Floor: user with role "cs_manager" must be permitted to perform action cancelOrder.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "cs_manager"
};
