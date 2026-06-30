// Floor: user with role "audit_read" must be permitted to perform action disputeOrder.
permit (
    principal is User,
    action == Action::"disputeOrder",
    resource is Order
)
when {
    principal.role == "audit_read"
};
