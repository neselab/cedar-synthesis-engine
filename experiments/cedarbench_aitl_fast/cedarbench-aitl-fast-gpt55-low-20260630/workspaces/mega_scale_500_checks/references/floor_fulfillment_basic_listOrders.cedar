// Floor: user with role "fulfillment_basic" must be permitted to perform action listOrders.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
