// Floor: a security_admin MUST be permitted to adminOverride an order with status=refunded.
permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
)
when {
    principal.role == "security_admin"
    && resource.status == "refunded"
};
