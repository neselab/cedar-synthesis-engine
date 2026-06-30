// Floor: user with role "fulfillment_manager" must be permitted to perform action listOrders.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
