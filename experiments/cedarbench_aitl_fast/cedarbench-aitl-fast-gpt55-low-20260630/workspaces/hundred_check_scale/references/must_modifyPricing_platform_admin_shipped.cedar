// Floor: a platform_admin MUST be permitted to modifyPricing an order with status=shipped.
permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
)
when {
    principal.role == "platform_admin"
    && resource.status == "shipped"
};
