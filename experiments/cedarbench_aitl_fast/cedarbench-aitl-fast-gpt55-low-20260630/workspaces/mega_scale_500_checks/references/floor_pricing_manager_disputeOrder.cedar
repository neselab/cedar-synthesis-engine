// Floor: user with role "pricing_manager" must be permitted to perform action disputeOrder.
permit (
    principal is User,
    action == Action::"disputeOrder",
    resource is Order
)
when {
    principal.role == "pricing_manager"
};
