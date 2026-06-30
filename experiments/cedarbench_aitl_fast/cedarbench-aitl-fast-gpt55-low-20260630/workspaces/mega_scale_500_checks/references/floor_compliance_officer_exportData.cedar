// Floor: user with role "compliance_officer" must be permitted to perform action exportData.
permit (
    principal is User,
    action == Action::"exportData",
    resource is Order
)
when {
    principal.role == "compliance_officer"
};
