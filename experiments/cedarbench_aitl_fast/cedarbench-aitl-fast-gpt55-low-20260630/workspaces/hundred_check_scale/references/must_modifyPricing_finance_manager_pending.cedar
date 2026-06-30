// Floor: a finance_manager MUST be permitted to modifyPricing an order with status=pending.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "finance_manager"
    && resource.status == "pending"
};
