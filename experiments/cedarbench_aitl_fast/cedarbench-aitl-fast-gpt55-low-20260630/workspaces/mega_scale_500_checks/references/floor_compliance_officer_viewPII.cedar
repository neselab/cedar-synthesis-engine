// Floor: user with role "compliance_officer" must be permitted to perform action viewPII.
permit (
    principal is User,
    action == Action::"viewPII",
    resource is Order
)
when {
    principal.role == "compliance_officer"
};
