// Floor: user with role "cs_manager" must be permitted to perform action disputeOrder.
permit (
    principal is User,
    action == Action::"disputeOrder",
    resource is Order
)
when {
    principal.role == "cs_manager"
};
