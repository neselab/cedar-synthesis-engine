// Floor: user with role "fulfillment_basic" must be permitted to perform action disputeOrder.
permit (
    principal is User,
    action == Action::"disputeOrder",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
