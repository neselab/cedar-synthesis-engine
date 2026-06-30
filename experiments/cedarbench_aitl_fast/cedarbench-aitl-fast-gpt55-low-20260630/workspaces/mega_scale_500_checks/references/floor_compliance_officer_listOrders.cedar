// Floor: user with role "compliance_officer" must be permitted to perform action listOrders.
permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
)
when {
    principal.role == "compliance_officer"
};
