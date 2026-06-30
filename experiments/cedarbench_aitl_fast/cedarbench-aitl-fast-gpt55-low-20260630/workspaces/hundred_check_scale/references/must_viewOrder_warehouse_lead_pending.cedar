// Floor: a warehouse_lead MUST be permitted to viewOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "warehouse_lead"
    && resource.status == "pending"
};
