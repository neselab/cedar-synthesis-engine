// Floor: user with role "warehouse" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "warehouse"
};
