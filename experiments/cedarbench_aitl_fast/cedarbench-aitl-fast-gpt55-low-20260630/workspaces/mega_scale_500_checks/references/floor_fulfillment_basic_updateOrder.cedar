// Floor: user with role "fulfillment_basic" must be permitted to perform action updateOrder.
permit (
    principal is User,
    action == Action::"updateOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
