// Floor: user with role "fulfillment_basic" must be permitted to perform action refundOrder.
permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
