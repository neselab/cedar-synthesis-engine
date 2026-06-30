// Floor: user with role "pricing_manager" must be permitted to perform action createOrder.
permit (
    principal is User,
    action == Action::"createOrder",
    resource is Order
)
when {
    principal.role == "pricing_manager"
};
