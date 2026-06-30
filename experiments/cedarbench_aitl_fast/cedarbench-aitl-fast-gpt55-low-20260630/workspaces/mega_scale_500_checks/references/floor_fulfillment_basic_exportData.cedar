// Floor: user with role "fulfillment_basic" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "fulfillment_basic"
};
