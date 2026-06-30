// Floor: user with role "finance_basic" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "finance_basic"
};
