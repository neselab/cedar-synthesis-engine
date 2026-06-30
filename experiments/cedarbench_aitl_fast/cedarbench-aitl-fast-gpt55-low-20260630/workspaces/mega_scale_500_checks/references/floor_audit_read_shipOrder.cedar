// Floor: user with role "audit_read" must be permitted to perform action shipOrder.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    principal.role == "audit_read"
};
