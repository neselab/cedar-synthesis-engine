// Floor: user with role "cs_manager" must be permitted to perform action updateOrder.
permit (
    principal is User,
    action == Action::"updateOrder",
    resource is Order
)
when {
    principal.role == "cs_manager"
};
