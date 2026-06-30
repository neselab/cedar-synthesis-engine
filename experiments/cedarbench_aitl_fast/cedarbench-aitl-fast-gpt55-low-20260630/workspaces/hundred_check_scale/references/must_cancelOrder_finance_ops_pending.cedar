// Floor: a finance_ops MUST be permitted to cancelOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "finance_ops"
    && resource.status == "pending"
};
