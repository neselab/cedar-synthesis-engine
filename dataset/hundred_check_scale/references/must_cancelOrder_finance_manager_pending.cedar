// Floor: a finance_manager MUST be permitted to cancelOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
)
when {
    principal.role == "finance_manager"
    && resource.status == "pending"
};
