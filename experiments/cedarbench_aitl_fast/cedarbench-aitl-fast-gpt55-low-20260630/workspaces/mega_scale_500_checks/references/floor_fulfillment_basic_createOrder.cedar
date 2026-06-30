// Floor: user with role "fulfillment_basic" must be permitted to perform action createOrder.
permit (
    principal is User,
    action == Action::"createOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
