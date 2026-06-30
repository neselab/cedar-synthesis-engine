// Floor: a cs_agent MUST be permitted to viewOrder an order with status=cart.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "cs_agent"
    && resource.status == "cart"
};
