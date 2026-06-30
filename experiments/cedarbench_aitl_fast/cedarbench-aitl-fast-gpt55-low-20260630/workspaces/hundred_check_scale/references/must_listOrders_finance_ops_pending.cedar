// Floor: a finance_ops MUST be permitted to listOrders an order with status=pending.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "finance_ops"
    && resource.status == "pending"
};
