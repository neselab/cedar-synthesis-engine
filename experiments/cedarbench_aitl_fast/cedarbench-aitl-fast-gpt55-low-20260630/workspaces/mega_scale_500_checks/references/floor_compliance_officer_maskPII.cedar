// Floor: user with role "compliance_officer" must be permitted to perform action maskPII.
permit (
    principal is User,
    action == Action::"maskPII",
    resource is Order
)
when {
    principal.role == "compliance_officer"
};
