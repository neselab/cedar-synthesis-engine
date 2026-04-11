// Floor: a finance_ops MUST be permitted to listOrders an order with status=refunded.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "finance_ops"
    && resource.status == "refunded"
};
