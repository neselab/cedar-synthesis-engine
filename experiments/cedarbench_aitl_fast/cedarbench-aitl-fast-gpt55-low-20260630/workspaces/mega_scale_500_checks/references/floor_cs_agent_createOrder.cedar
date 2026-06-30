// Floor: user with role "cs_agent" must be permitted to perform action createOrder.
permit (
    principal is User,
    action == Action::"createOrder",
    resource is Order
)
when {
    principal.role == "cs_agent"
};
