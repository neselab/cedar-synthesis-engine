// Floor: user with role "risk_analyst" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "risk_analyst"
};
