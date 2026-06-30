// Floor: a platform_admin MUST be permitted to viewOrder an order with status=refunded.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "platform_admin"
    && resource.status == "refunded"
};
