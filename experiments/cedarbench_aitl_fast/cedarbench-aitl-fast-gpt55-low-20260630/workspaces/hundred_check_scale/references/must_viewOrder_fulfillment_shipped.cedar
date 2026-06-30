// Floor: a fulfillment MUST be permitted to viewOrder an order with status=shipped.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "fulfillment"
    && resource.status == "shipped"
};
