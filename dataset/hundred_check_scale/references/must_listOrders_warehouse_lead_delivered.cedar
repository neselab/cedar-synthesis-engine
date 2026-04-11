// Floor: a warehouse_lead MUST be permitted to listOrders an order with status=delivered.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "warehouse_lead"
    && resource.status == "delivered"
};
