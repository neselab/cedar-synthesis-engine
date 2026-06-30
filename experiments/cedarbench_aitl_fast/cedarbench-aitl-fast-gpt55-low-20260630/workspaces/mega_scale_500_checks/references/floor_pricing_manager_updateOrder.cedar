// Floor: user with role "pricing_manager" must be permitted to perform action updateOrder.
permit (
    principal is User,
    action == Action::"updateOrder",
    resource is Order
)
when {
    principal.role == "pricing_manager"
};
