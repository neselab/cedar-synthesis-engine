// Floor: a security_admin MUST be permitted to adminOverride an order with status=shipped.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "security_admin"
    && resource.status == "shipped"
};
