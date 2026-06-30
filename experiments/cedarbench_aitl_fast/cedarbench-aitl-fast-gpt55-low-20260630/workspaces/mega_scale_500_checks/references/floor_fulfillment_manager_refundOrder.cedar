// Floor: user with role "fulfillment_manager" must be permitted to perform action refundOrder.
permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
