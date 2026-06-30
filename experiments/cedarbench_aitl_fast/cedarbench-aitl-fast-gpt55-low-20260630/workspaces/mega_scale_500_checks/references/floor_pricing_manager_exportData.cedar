// Floor: user with role "pricing_manager" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "pricing_manager"
};
