// Floor: a platform_admin MUST be permitted to modifyPricing an order with status=refunded.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "platform_admin"
    && resource.status == "refunded"
};
