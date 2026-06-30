// Floor: user with role "warehouse" must be permitted to perform action createOrder.
permit (
    principal is User,
    action == Action::"createOrder",
    resource is Order
)
when {
    principal.role == "warehouse"
};
