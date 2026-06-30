// Floor: a warehouse_lead MUST be permitted to viewOrder an order with status=cart.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "warehouse_lead"
    && resource.status == "cart"
};
