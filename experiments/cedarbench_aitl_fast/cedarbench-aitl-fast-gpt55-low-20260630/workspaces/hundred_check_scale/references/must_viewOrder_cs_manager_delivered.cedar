// Floor: a cs_manager MUST be permitted to viewOrder an order with status=delivered.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "cs_manager"
    && resource.status == "delivered"
};
