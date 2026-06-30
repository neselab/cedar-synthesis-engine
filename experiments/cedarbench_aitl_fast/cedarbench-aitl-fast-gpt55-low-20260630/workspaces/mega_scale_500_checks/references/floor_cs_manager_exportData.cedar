// Floor: user with role "cs_manager" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "cs_manager"
};
