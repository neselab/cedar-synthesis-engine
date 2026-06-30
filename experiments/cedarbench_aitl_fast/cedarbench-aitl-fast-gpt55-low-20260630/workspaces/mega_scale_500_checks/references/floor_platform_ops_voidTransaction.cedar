// Floor: user with role "platform_ops" must be permitted to perform action voidTransaction.
permit (
    principal is User,
    action == Action::"voidTransaction",
    resource is Order
)
when {
    principal.role == "platform_ops"
};
