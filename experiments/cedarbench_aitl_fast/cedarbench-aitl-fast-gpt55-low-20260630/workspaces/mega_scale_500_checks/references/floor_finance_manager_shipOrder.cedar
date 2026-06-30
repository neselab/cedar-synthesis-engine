// Floor: user with role "finance_manager" must be permitted to perform action shipOrder.
permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
)
when {
    principal.role == "finance_manager"
};
