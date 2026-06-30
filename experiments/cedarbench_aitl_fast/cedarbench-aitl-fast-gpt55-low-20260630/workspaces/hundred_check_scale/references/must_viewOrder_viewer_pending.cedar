// Floor: a viewer MUST be permitted to viewOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "viewer"
    && resource.status == "pending"
};
