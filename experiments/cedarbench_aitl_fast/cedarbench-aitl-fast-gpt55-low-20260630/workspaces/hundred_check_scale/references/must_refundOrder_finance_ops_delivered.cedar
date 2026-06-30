// Floor: a finance_ops MUST be permitted to refundOrder an order with status=delivered.
permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
)
when {
    principal.role == "finance_ops"
    && resource.status == "delivered"
};
