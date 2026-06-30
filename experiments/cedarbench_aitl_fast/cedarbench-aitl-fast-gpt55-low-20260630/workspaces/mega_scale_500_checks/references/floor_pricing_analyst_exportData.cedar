// Floor: user with role "pricing_analyst" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "pricing_analyst"
};
