// Floor: user with role "compliance_officer" must be permitted to perform action viewOrder.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "compliance_officer"
};
