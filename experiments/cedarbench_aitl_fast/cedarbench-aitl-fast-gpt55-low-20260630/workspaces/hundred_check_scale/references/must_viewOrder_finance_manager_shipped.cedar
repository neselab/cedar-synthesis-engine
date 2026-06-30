// Floor: a finance_manager MUST be permitted to viewOrder an order with status=shipped.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "finance_manager"
    && resource.status == "shipped"
};
