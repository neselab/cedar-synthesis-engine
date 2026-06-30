// Floor: a warehouse_lead MUST be permitted to shipOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    principal.role == "warehouse_lead"
    && resource.status == "pending"
};
