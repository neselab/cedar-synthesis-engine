// Floor: user with role "security_admin" must be permitted to perform action updateOrder.
permit (
    principal is User,
    action == Action::"updateOrder",
    resource is Order
)
when {
    principal.role == "security_admin"
};
