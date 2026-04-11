// Floor: a finance_manager MUST be permitted to modifyPricing an order with status=shipped.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "finance_manager"
    && resource.status == "shipped"
};
