// Floor: user with role "fulfillment_manager" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "fulfillment_manager"
};
