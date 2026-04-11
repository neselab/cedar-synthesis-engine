// Floor: a cs_agent MUST be permitted to cancelOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "cs_agent"
    && resource.status == "pending"
};
