// Floor: user with role "fulfillment_manager" must be permitted to perform action bulkOperations.
permit (
    principal is User,
    action == Action::"bulkOperations",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
