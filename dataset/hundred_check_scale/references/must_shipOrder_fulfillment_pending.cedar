// Floor: a fulfillment MUST be permitted to shipOrder an order with status=pending.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    principal.role == "fulfillment"
    && resource.status == "pending"
};
