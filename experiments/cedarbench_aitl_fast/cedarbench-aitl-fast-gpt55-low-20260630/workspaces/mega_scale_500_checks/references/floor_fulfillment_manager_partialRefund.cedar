// Floor: user with role "fulfillment_manager" must be permitted to perform action partialRefund.
permit (
    principal is User,
    action == Action::"partialRefund",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
