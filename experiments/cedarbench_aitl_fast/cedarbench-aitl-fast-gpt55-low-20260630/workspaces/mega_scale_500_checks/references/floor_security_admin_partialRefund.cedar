// Floor: user with role "security_admin" must be permitted to perform action partialRefund.
permit (
    principal is User,
    action == Action::"partialRefund",
    resource is Order
)
when {
    principal.role == "security_admin"
};
