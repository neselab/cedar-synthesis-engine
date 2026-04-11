// Floor: a platform_admin MUST be permitted to viewOrder an order with status=delivered.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "platform_admin"
    && resource.status == "delivered"
};
