// Floor: user with role "platform_ops" must be permitted to perform action partialRefund.
permit (
    principal is User,
    action == Action::"partialRefund",
    resource is Order
)
when {
    principal.role == "platform_ops"
};
