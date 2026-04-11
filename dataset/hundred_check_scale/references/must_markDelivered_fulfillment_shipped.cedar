// Floor: a fulfillment MUST be permitted to markDelivered an order with status=shipped.
permit (
    principal is User,
    action == Action::"markDelivered",
    resource is Order
)
when {
    principal.role == "fulfillment"
    && resource.status == "shipped"
};
