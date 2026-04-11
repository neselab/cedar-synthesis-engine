// Floor: a finance_manager MUST be permitted to listOrders an order with status=delivered.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "finance_manager"
    && resource.status == "delivered"
};
