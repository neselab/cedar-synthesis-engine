// Floor: a cs_agent MUST be permitted to placeOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"placeOrder",
    resource is Order
)
when {
    principal.role == "cs_agent"
    && resource.status == "pending"
};
