// Floor: user with role "audit_read" must be permitted to perform action viewOrder.
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
)
when {
    principal.role == "audit_read"
};
