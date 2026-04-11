// Floor: a security_admin MUST be permitted to viewOrder an order with status=shipped.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "security_admin"
    && resource.status == "shipped"
};
